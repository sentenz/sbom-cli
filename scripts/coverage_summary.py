"""Render a GitHub-friendly Markdown summary from pytest-cov Cobertura XML.

The renderer uses only the Python standard library. This matters in CI: a test
setup failure must still produce a useful "coverage unavailable" job summary.
"""

from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path
from xml.etree import ElementTree


def _nonnegative_integer(value: str | None, attribute: str) -> int:
    if value is None:
        raise ValueError(f"Missing Cobertura attribute: {attribute}")
    parsed = int(value)
    if parsed < 0:
        raise ValueError(f"Negative Cobertura attribute: {attribute}")
    return parsed


def _rate(value: str | None, attribute: str) -> float:
    if value is None:
        raise ValueError(f"Missing Cobertura attribute: {attribute}")
    number = float(value)
    if not math.isfinite(number) or not 0 <= number <= 1:
        raise ValueError(f"Invalid Cobertura rate: {attribute}")
    return number


def _status(rate: float) -> str:
    if rate >= 0.8:
        return "🟢 High"
    if rate >= 0.6:
        return "🟡 Moderate"
    return "🔴 Low"


def _escape_cell(value: str) -> str:
    """Treat XML-sourced filenames as text, not Markdown or HTML."""
    return (
        value.replace("&", "&amp;")
        .replace("|", "&#124;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace("\n", " ")
        .replace("\r", " ")
    )


def render_coverage(xml: str) -> str:
    """Produce a total and per-file coverage report from Cobertura XML."""
    root = ElementTree.fromstring(xml)
    if root.tag != "coverage":
        raise ValueError("Expected a Cobertura <coverage> root element")

    lines = _nonnegative_integer(root.get("lines-valid"), "lines-valid")
    covered_lines = _nonnegative_integer(root.get("lines-covered"), "lines-covered")
    branches = _nonnegative_integer(root.get("branches-valid"), "branches-valid")
    covered_branches = _nonnegative_integer(root.get("branches-covered"), "branches-covered")
    if covered_lines > lines or covered_branches > branches:
        raise ValueError("Covered statements/branches exceed totals")

    output = [
        "## Python code coverage",
        "",
        "| Metric | Coverage | Covered / total | Level |",
        "| --- | ---: | ---: | --- |",
    ]

    for name, covered, total in (
        ("Lines", covered_lines, lines),
        ("Branches", covered_branches, branches),
    ):
        if total:
            percentage = covered / total
            output.append(
                f"| {name} | **{percentage:.1%}** | {covered} / {total} | "
                f"{_status(percentage)} |"
            )
        else:
            output.append(f"| {name} | n/a | {covered} / {total} | n/a |")

    file_rows: list[tuple[str, str, str]] = []
    for element in root.findall(".//class"):
        name = element.get("filename")
        if not name:
            continue
        line_rate = _rate(element.get("line-rate"), "class line-rate")
        has_branches = any(line.get("branch") == "true" for line in element.findall("./lines/line"))
        branch_rate = (
            f"{_rate(element.get('branch-rate'), 'class branch-rate'):.1%}"
            if has_branches
            else "n/a"
        )
        file_rows.append((name, f"{line_rate:.1%}", branch_rate))

    if file_rows:
        output.extend(
            [
                "",
                "### File coverage",
                "",
                "| File | Lines | Branches |",
                "| --- | ---: | ---: |",
            ]
        )
        for filename, line_rate, branch_rate in sorted(file_rows)[:50]:
            output.append(
                f"| `{_escape_cell(filename)}` | {line_rate} | {branch_rate} |"
            )
        if len(file_rows) > 50:
            output.append(f"\n_Additional files omitted: {len(file_rows) - 50}._")

    output.extend(
        [
            "",
            "_Coverage levels: High ≥80%; Moderate ≥60%; Low <60%. "
            "Computed from pytest-cov XML; Atheris fuzz campaigns are reported separately._",
            "",
        ]
    )
    return "\n".join(output)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--xml", type=Path, default=Path("logs/coverage.xml"))
    parser.add_argument("--output", type=Path, default=Path("logs/coverage-summary.md"))
    parser.add_argument("--job-summary", type=Path)
    args = parser.parse_args(argv)

    failure = False
    if not args.xml.is_file():
        markdown = (
            "## Python code coverage\n\n"
            "Coverage unavailable: `logs/coverage.xml` was not produced. "
            "Inspect the Python test step and attached artifacts.\n"
        )
    else:
        try:
            markdown = render_coverage(args.xml.read_text(encoding="utf-8"))
        except (OSError, ValueError, ElementTree.ParseError) as error:
            failure = True
            markdown = (
                "## Python code coverage\n\n"
                "Coverage unavailable: the XML report could not be parsed. "
                "Inspect the coverage artifact and reporting step.\n"
            )
            print(f"Coverage summary error: {error}", file=sys.stderr)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(markdown, encoding="utf-8")
    if args.job_summary is not None:
        with args.job_summary.open("a", encoding="utf-8") as destination:
            destination.write(markdown + "\n")
    print(f"Coverage summary written to {args.output}")
    return 1 if failure else 0


if __name__ == "__main__":
    raise SystemExit(main())
