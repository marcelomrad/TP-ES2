from __future__ import annotations

import csv
import json
from pathlib import Path

from repo_miner.models import AnalysisResult

SUPPORTED_FORMATS = {"csv", "json", "md"}


def result_summary(result: AnalysisResult) -> dict[str, str | int | None]:
    return {
        "repository": str(result.repository),
        "commits_analyzed": result.commits_analyzed,
        "files_seen": result.files_seen,
        "files_analyzed": result.files_analyzed,
        "since": result.since.isoformat() if result.since else None,
        "until": result.until.isoformat() if result.until else None,
    }


def write_report(result: AnalysisResult, output: Path, output_format: str) -> Path:
    normalized_format = output_format.lower()
    if normalized_format not in SUPPORTED_FORMATS:
        supported = ", ".join(sorted(SUPPORTED_FORMATS))
        raise ValueError(f"Unsupported report format '{output_format}'. Supported: {supported}.")

    output = output.expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)

    if normalized_format == "csv":
        write_csv(result, output)
    elif normalized_format == "json":
        write_json(result, output)
    else:
        write_markdown(result, output)

    return output


def write_csv(result: AnalysisResult, output: Path) -> None:
    rows = [hotspot.to_row() for hotspot in result.hotspots]
    fieldnames = list(rows[0].keys()) if rows else [
        "path",
        "risk",
        "score",
        "commits",
        "line_churn",
        "added_lines",
        "deleted_lines",
        "authors",
        "total_complexity",
        "max_function_complexity",
        "average_function_complexity",
        "functions",
        "nloc",
    ]

    with output.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_json(result: AnalysisResult, output: Path) -> None:
    payload = {
        "summary": result_summary(result),
        "hotspots": [hotspot.to_row() for hotspot in result.hotspots],
    }
    output.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def write_markdown(result: AnalysisResult, output: Path) -> None:
    lines = [
        "# Relatorio de hot spots",
        "",
        f"- Repositorio: `{result.repository}`",
        f"- Commits analisados: {result.commits_analyzed}",
        f"- Arquivos vistos no historico: {result.files_seen}",
        f"- Arquivos analisados: {result.files_analyzed}",
        "",
        "| Rank | Risco | Score | Arquivo | Commits | Churn | CC total | CC max | NLOC |",
        "|---:|---|---:|---|---:|---:|---:|---:|---:|",
    ]

    for index, hotspot in enumerate(result.hotspots, start=1):
        lines.append(
            "| "
            f"{index} | {hotspot.risk} | {hotspot.score:.2f} | `{hotspot.path}` | "
            f"{hotspot.commits} | {hotspot.line_churn} | {hotspot.total_complexity} | "
            f"{hotspot.max_function_complexity} | {hotspot.nloc} |"
        )

    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
