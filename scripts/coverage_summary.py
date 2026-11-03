"""Render pytest-cov XML as Markdown using only the standard library."""

from __future__ import annotations

import argparse
import html
import os
import sys
from pathlib import Path
from xml.etree import ElementTree


def _percentage(value: str) -> str:
    rate = float(value)
    if not 0 <= rate <= 1:
        raise ValueError(f"Invalid coverage rate: {value}")
    return f"{rate:.1%}"


def _status(rate: float) -> str:
    if rate >= 0.8:
        return "🟢 High"
    if rate >= 0.6:
        return "🟡 Moderate"
    return "🔴 Low"


def _escape_cell(value: str) -> str:
    return (
        html.escape(value, quote=False)
        .replace("|", "&#124;")
        .replace("`", "&#96;")
        .replace("\n", " ")
        .replace("\r", " ")
    )


def render_coverage(xml: str) -> str:
    """Return overall and per-file line/branch coverage as Markdown."""
    root = ElementTree.fromstring(xml)
    if root.tag != "coverage":
        raise ValueError("Expected a Cobertura <coverage> root element")
    rows = [
        "## Python code coverage",
        "",
        "| Metric | Coverage | Covered / total | Level |",
        "| --- | ---: | ---: | --- |",
    ]
    for metric in ("lines", "branches"):
        covered = int(root.attrib[f"{metric}-covered"])
        total = int(root.attrib[f"{metric}-valid"])
        if not 0 <= covered <= total:
            raise ValueError(f"Invalid {metric} totals: {covered} / {total}")
        percent = f"**{covered / total:.1%}**" if total else "n/a"
        level = _status(covered / total) if total else "n/a"
        rows.append(
            f"| {metric.capitalize()} | {percent} | {covered} / {total} | {level} |"
        )

    files = sorted(
        (entry for entry in root.findall(".//class") if entry.get("filename")),
        key=lambda entry: entry.attrib["filename"],
    )
    if files:
        rows += [
            "",
            "### File coverage",
            "",
            "| File | Lines | Branches |",
            "| --- | ---: | ---: |",
        ]
    for entry in files[:50]:
        name = _escape_cell(entry.attrib["filename"])
        lines = _percentage(entry.attrib["line-rate"])
        has_branches = any(
            line.get("branch") == "true"
            for line in entry.findall("./lines/line")
        )
        branches = (
            _percentage(entry.attrib["branch-rate"]) if has_branches else "n/a"
        )
        rows.append(f"| `{name}` | {lines} | {branches} |")
    if len(files) > 50:
        rows.append(f"\n_Additional files omitted: {len(files) - 50}._")
    rows += ["", "_Coverage levels: High ≥80%; Moderate ≥60%; Low <60%._", ""]
    return "\n".join(rows)


def main(argv: list[str] | None = None) -> int:
    """Write the report artifact and, in Actions, append the same job summary."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--xml", type=Path, default=Path("logs/coverage.xml"))
    parser.add_argument(
        "--output", type=Path, default=Path("logs/coverage-summary.md")
    )
    parser.add_argument(
        "--job-summary", type=Path, default=os.getenv("GITHUB_STEP_SUMMARY")
    )
    args = parser.parse_args(argv)
    status = 0
    markdown = (
        "## Python code coverage\n\nCoverage unavailable. "
        "Inspect the Python test step and attached artifacts.\n"
    )
    try:
        markdown = render_coverage(args.xml.read_text(encoding="utf-8"))
    except FileNotFoundError:
        pass  # Setup failures can leave no XML; still publish an explanation.
    except (OSError, ValueError, KeyError, ElementTree.ParseError) as error:
        status = 1
        print(f"Coverage summary error: {error}", file=sys.stderr)

    server = os.getenv("GITHUB_SERVER_URL")
    repo = os.getenv("GITHUB_REPOSITORY")
    run_id = os.getenv("GITHUB_RUN_ID")
    if server and repo and run_id:
        markdown += f"\n[Workflow run]({server}/{repo}/actions/runs/{run_id})\n"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(markdown, encoding="utf-8")
    if args.job_summary is not None:
        with args.job_summary.open("a", encoding="utf-8") as destination:
            destination.write(markdown + "\n")
    print(f"Coverage summary written to {args.output}")
    return status


if __name__ == "__main__":
    raise SystemExit(main())
