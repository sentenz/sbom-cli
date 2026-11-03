"""Black-box tests for the CI Cobertura summary renderer."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "coverage_summary.py"

COVERAGE = """<coverage lines-covered="8" lines-valid="10"
  branches-covered="1" branches-valid="2" line-rate="0.8" branch-rate="0.5">
  <packages><package name="sbom"><classes>
    <class name="Client" filename="sbom/client.py" line-rate="0.8" branch-rate="0.5">
      <lines><line number="1" hits="1" branch="true"/>
      <line number="2" hits="0"/></lines>
    </class>
    <class name="Config" filename="sbom/config.py" line-rate="1" branch-rate="0">
      <lines><line number="1" hits="1"/></lines>
    </class>
  </classes></package></packages>
</coverage>"""


def _run(
    tmp_path: Path, xml: str | None
) -> tuple[subprocess.CompletedProcess[str], str, str]:
    report = tmp_path / "coverage.xml"
    output = tmp_path / "summary.md"
    job_summary = tmp_path / "job-summary.md"
    if xml is not None:
        report.write_text(xml, encoding="utf-8")
    completed = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--xml",
            str(report),
            "--output",
            str(output),
            "--job-summary",
            str(job_summary),
        ],
        capture_output=True,
        text=True,
        check=False,
        timeout=10,
    )
    return (
        completed,
        output.read_text(encoding="utf-8"),
        job_summary.read_text(encoding="utf-8"),
    )


def test_total_and_per_file_coverage(tmp_path: Path) -> None:
    completed, markdown, job_summary = _run(tmp_path, COVERAGE)
    assert completed.returncode == 0
    assert "**80.0%**" in markdown
    assert "**50.0%**" in markdown
    assert "8 / 10" in markdown
    assert "1 / 2" in markdown
    assert "🟢 High" in markdown
    assert "🔴 Low" in markdown
    assert "| `sbom/client.py` | 80.0% | 50.0% |" in markdown
    assert "| `sbom/config.py` | 100.0% | n/a |" in markdown
    assert markdown in job_summary


def test_missing_report_produces_explanation(tmp_path: Path) -> None:
    completed, markdown, job_summary = _run(tmp_path, None)
    assert completed.returncode == 0
    assert "Coverage unavailable" in markdown
    assert "Coverage unavailable" in job_summary


def test_malformed_report_fails_without_silent_success(tmp_path: Path) -> None:
    completed, markdown, _ = _run(tmp_path, "<coverage")
    assert completed.returncode == 1
    assert "Coverage summary error" in completed.stderr
    assert "Coverage unavailable" in markdown


def test_escaped_filenames(tmp_path: Path) -> None:
    xml = COVERAGE.replace("sbom/client.py", "sbom/cli|build&lt;test&gt;.py")
    completed, markdown, _ = _run(tmp_path, xml)
    assert completed.returncode == 0
    assert "cli&#124;build&lt;test&gt;.py" in markdown


def test_rejects_invalid_totals(tmp_path: Path) -> None:
    xml = COVERAGE.replace('lines-covered="8"', 'lines-covered="11"')
    completed, markdown, _ = _run(tmp_path, xml)
    assert completed.returncode == 1
    assert "Coverage unavailable" in markdown


def test_default_paths_and_actions_summary(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    logs = tmp_path / "logs"
    logs.mkdir()
    (logs / "coverage.xml").write_text(COVERAGE, encoding="utf-8")
    summary = tmp_path / "job-summary.md"
    summary.write_text("Existing summary\n", encoding="utf-8")
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary))
    monkeypatch.setenv("GITHUB_SERVER_URL", "https://github.com")
    monkeypatch.setenv("GITHUB_REPOSITORY", "sentenz/sbom-cli")
    monkeypatch.setenv("GITHUB_RUN_ID", "123")
    subprocess.run(
        [sys.executable, str(SCRIPT)], cwd=tmp_path, check=True, timeout=10
    )
    markdown = (logs / "coverage-summary.md").read_text(encoding="utf-8")
    assert "https://github.com/sentenz/sbom-cli/actions/runs/123" in markdown
    assert (
        summary.read_text(encoding="utf-8")
        == "Existing summary\n" + markdown + "\n"
    )
