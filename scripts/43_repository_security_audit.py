#!/usr/bin/env python3
"""
JAS-JESI Independent Repository Security Audit

Purpose:
    Independent security, reproducibility, CI-policy, and Python validation
    for JAS-JESI Master Version 1.0.

Important:
    This script MUST NOT modify:
      - JESI methodology
      - production formulas
      - indicator weights
      - research-validation sequence
      - empirical results

The audit produces evidence. It does not replace human methodological review.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

WORKFLOWS_DIR = ROOT / ".github" / "workflows"
REQUIREMENTS_FILE = ROOT / "requirements.txt"

AUDIT_DIR = ROOT / "audit"
REPORT_FILE = AUDIT_DIR / "repository-audit.json"
PIP_AUDIT_FILE = AUDIT_DIR / "pip-audit.json"

EXPECTED_PYTHON = "3.10"

# Fixed scanner version for deterministic audit tooling.
PIP_AUDIT_VERSION = "2.10.1"


results: list[dict[str, str]] = []
failures: list[str] = []
warnings: list[str] = []


def record(check: str, status: str, detail: str) -> None:
    """Record an audit result."""

    results.append(
        {
            "check": check,
            "status": status,
            "detail": detail,
        }
    )

    if status == "FAIL":
        failures.append(f"{check}: {detail}")

    elif status == "WARN":
        warnings.append(f"{check}: {detail}")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


# ==============================================================
# REQUIREMENTS AUDIT
# ==============================================================


def audit_requirements() -> None:
    """Validate requirements.txt exact version pinning."""

    if not REQUIREMENTS_FILE.exists():
        record(
            "requirements.exists",
            "FAIL",
            "requirements.txt is missing.",
        )
        return

    lines = []

    for raw_line in read_text(REQUIREMENTS_FILE).splitlines():
        line = raw_line.strip()

        if not line:
            continue

        if line.startswith("#"):
            continue

        lines.append(line)

    if not lines:
        record(
            "requirements.nonempty",
            "FAIL",
            "requirements.txt contains no dependencies.",
        )
        return

    unpinned = []

    exact_pin_pattern = re.compile(
        r"^[A-Za-z0-9_.-]+\s*==\s*[^ \t#]+$"
    )

    for line in lines:
        if not exact_pin_pattern.match(line):
            unpinned.append(line)

    if unpinned:
        record(
            "requirements.exact-pins",
            "FAIL",
            "Non-exact dependency specifications found: "
            + ", ".join(unpinned),
        )
    else:
        record(
            "requirements.exact-pins",
            "PASS",
            f"All {len(lines)} dependency entries use exact == pins.",
        )

    # Lock strategy is intentionally not enforced yet because it is
    # a later phase in the locked JAS-JESI execution order.
    record(
        "requirements.lock",
        "WARN",
        (
            "No lock/hashed requirements file is currently enforced. "
            "Dependency lock/reproducibility strategy remains a later "
            "Master 1.0 hardening phase."
        ),
    )


# ==============================================================
# WORKFLOW DISCOVERY
# ==============================================================


def get_workflow_files() -> list[Path]:
    """Return GitHub Actions workflow files."""

    if not WORKFLOWS_DIR.exists():
        record(
            "workflows.exists",
            "FAIL",
            ".github/workflows directory is missing.",
        )
        return []

    files = sorted(
        list(WORKFLOWS_DIR.glob("*.yml"))
        + list(WORKFLOWS_DIR.glob("*.yaml"))
    )

    if not files:
        record(
            "workflows.present",
            "FAIL",
            "No GitHub Actions workflow files found.",
        )
        return []

    record(
        "workflows.present",
        "PASS",
        f"Found {len(files)} workflow files.",
    )

    return files


# ==============================================================
# ACTION SHA AUDIT
# ==============================================================


def audit_action_sha(path: Path, text: str, rel: str) -> None:
    """Require GitHub Actions references to use immutable commit SHAs."""

    uses = re.findall(
        r"^\s*uses:\s*([^\s#]+)",
        text,
        flags=re.MULTILINE,
    )

    if not uses:
        record(
            f"workflow.action-sha.{rel}",
            "PASS",
            "No GitHub Action references found.",
        )
        return

    unpinned = []

    for reference in uses:
        if "@" not in reference:
            unpinned.append(reference)
            continue

        ref = reference.rsplit("@", 1)[1]

        if not re.fullmatch(r"[0-9a-fA-F]{40}", ref):
            unpinned.append(reference)

    if unpinned:
        record(
            f"workflow.action-sha.{rel}",
            "FAIL",
            (
                "Action references are not immutable 40-character "
                "commit SHAs: "
                + ", ".join(unpinned)
            ),
        )
    else:
        record(
            f"workflow.action-sha.{rel}",
            "PASS",
            (
                f"All {len(uses)} GitHub Action references use "
                "40-character commit SHAs."
            ),
        )


# ==============================================================
# PYTHON VERSION AUDIT
# ==============================================================


def audit_python_baseline(path: Path, text: str, rel: str) -> None:
    """Ensure explicitly configured Python versions remain at 3.10."""

    versions = re.findall(
        r"""python-version:\s*["']?([^"'\s]+)""",
        text,
    )

    if not versions:
        record(
            f"workflow.python-baseline.{rel}",
            "PASS",
            "No explicit Python version configured in this workflow.",
        )
        return

    invalid = [
        version
        for version in versions
        if version != EXPECTED_PYTHON
    ]

    if invalid:
        record(
            f"workflow.python-baseline.{rel}",
            "FAIL",
            (
                f"Python versions {invalid} conflict with the "
                f"frozen Python {EXPECTED_PYTHON} baseline."
            ),
        )
    else:
        record(
            f"workflow.python-baseline.{rel}",
            "PASS",
            (
                f"All explicit Python versions use the frozen "
                f"Python {EXPECTED_PYTHON} baseline."
            ),
        )


# ==============================================================
# PERMISSION AUDIT
# ==============================================================


def audit_write_permissions(path: Path, text: str, rel: str) -> None:
    """
    Audit contents: write permissions.

    Policy:
      - Read-only is the default.
      - final-jesi.yml may have contents: write ONLY inside
        the dedicated commit-results job.
      - Other workflows must not request repository write access.
    """

    matches = list(
        re.finditer(
            r"(?m)^([ \t]*)contents:\s*write\s*$",
            text,
        )
    )

    if not matches:
        record(
            f"workflow.write-permission.{rel}",
            "PASS",
            "No contents: write permission declared.",
        )
        return

    if rel != ".github/workflows/final-jesi.yml":
        record(
            f"workflow.write-permission.{rel}",
            "FAIL",
            (
                "contents: write is declared outside the authorized "
                "final JESI output-commit workflow."
            ),
        )
        return

    # For final-jesi.yml, every write permission must occur inside
    # the commit-results job.
    commit_job_match = re.search(
        r"(?m)^  commit-results:\s*$",
        text,
    )

    if not commit_job_match:
        record(
            f"workflow.write-permission.{rel}",
            "FAIL",
            (
                "contents: write exists, but the expected "
                "commit-results job was not found."
            ),
        )
        return

    commit_job_start = commit_job_match.start()

    next_job_match = re.search(
        r"(?m)^  [A-Za-z0-9_-]+:\s*$",
        text[commit_job_start + 1 :],
    )

    if next_job_match:
        commit_job_end = (
            commit_job_start
            + 1
            + next_job_match.start()
        )
    else:
        commit_job_end = len(text)

    unauthorized = []

    for match in matches:
        position = match.start()

        if not (
            commit_job_start
            <= position
            < commit_job_end
        ):
            unauthorized.append(match.group(0).strip())

    if unauthorized:
        record(
            f"workflow.write-permission.{rel}",
            "FAIL",
            (
                "contents: write exists outside the dedicated "
                "commit-results job."
            ),
        )
    else:
        record(
            f"workflow.write-permission.{rel}",
            "PASS",
            (
                "Repository write permission is restricted to "
                "the dedicated commit-results job."
            ),
        )


# ==============================================================
# CHECKOUT CREDENTIAL AUDIT
# ==============================================================


def audit_checkout_credentials(path: Path, text: str, rel: str) -> None:
    """
    Audit persist-credentials.

    Policy:
      - Normal computational workflows should use false.
      - final-jesi.yml may use true only for commit-results.
    """

    matches = list(
        re.finditer(
            r"(?m)^\s*persist-credentials:\s*true\s*$",
            text,
        )
    )

    if not matches:
        record(
            f"workflow.credentials.{rel}",
            "PASS",
            "No persist-credentials: true detected.",
        )
        return

    if rel != ".github/workflows/final-jesi.yml":
        record(
            f"workflow.credentials.{rel}",
            "FAIL",
            (
                "persist-credentials: true exists outside the "
                "authorized final-results commit workflow."
            ),
        )
        return

    commit_job_match = re.search(
        r"(?m)^  commit-results:\s*$",
        text,
    )

    if not commit_job_match:
        record(
            f"workflow.credentials.{rel}",
            "FAIL",
            (
                "Persistent credentials exist, but the expected "
                "commit-results job was not found."
            ),
        )
        return

    commit_start = commit_job_match.start()

    unauthorized = []

    for match in matches:
        if match.start() < commit_start:
            unauthorized.append(match.group(0))

    if unauthorized:
        record(
            f"workflow.credentials.{rel}",
            "FAIL",
            (
                "Persistent checkout credentials exist outside "
                "the authorized commit-results job."
            ),
        )
    else:
        record(
            f"workflow.credentials.{rel}",
            "PASS",
            (
                "Persistent checkout credentials are restricted "
                "to the authorized commit-results path."
            ),
        )


# ==============================================================
# REMOTE SHELL AUDIT
# ==============================================================


def audit_remote_shell(path: Path, text: str, rel: str) -> None:
    """Detect common curl/wget-to-shell execution patterns."""

    patterns = [
        r"curl\s+[^\n|]+\|\s*(bash|sh)",
        r"wget\s+[^\n|]+\|\s*(bash|sh)",
    ]

    found = []

    for pattern in patterns:
        if re.search(
            pattern,
            text,
            flags=re.IGNORECASE,
        ):
            found.append(pattern)

    if found:
        record(
            f"workflow.remote-shell.{rel}",
            "FAIL",
            "Remote content is piped directly into a shell.",
        )
    else:
        record(
            f"workflow.remote-shell.{rel}",
            "PASS",
            "No curl/wget-to-shell execution pattern detected.",
        )


# ==============================================================
# PYTHON SYNTAX AUDIT
# ==============================================================


def audit_python_syntax() -> None:
    """Compile repository Python code without executing research logic."""

    python_files = []

    for directory in ("scripts", "src"):
        target = ROOT / directory

        if target.exists():
            python_files.extend(
                target.rglob("*.py")
            )

    if not python_files:
        record(
            "python.files",
            "FAIL",
            "No Python files found under scripts/ or src/.",
        )
        return

    command = [
        sys.executable,
        "-m",
        "compileall",
        "-q",
        "scripts",
        "src",
    ]

    completed = subprocess.run(
        command,
        cwd=ROOT,
        capture_output=True,
        text=True,
    )

    if completed.returncode != 0:
        detail = (
            completed.stdout
            + completed.stderr
        ).strip()

        record(
            "python.syntax",
            "FAIL",
            detail or "Python compileall failed.",
        )
    else:
        record(
            "python.syntax",
            "PASS",
            (
                f"Python syntax compilation passed for "
                f"{len(python_files)} Python files."
            ),
        )


# ==============================================================
# PIP-AUDIT SECURITY SCAN
# ==============================================================


def audit_dependencies() -> None:
    """
    Install a fixed pip-audit version and scan requirements.txt.

    The scanner installation does not modify requirements.txt.
    """

    if not REQUIREMENTS_FILE.exists():
        record(
            "security.pip-audit",
            "FAIL",
            "Cannot scan dependencies because requirements.txt is missing.",
        )
        return

    AUDIT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    install_command = [
        sys.executable,
        "-m",
        "pip",
        "install",
        f"pip-audit=={PIP_AUDIT_VERSION}",
    ]

    install = subprocess.run(
        install_command,
        cwd=ROOT,
        capture_output=True,
        text=True,
    )

    if install.returncode != 0:
        detail = (
            install.stdout
            + install.stderr
        ).strip()

        record(
            "security.pip-audit-install",
            "FAIL",
            detail[-4000:] or "pip-audit installation failed.",
        )
        return

    scan_command = [
        sys.executable,
        "-m",
        "pip_audit",
        "-r",
        str(REQUIREMENTS_FILE),
        "--format",
        "json",
        "--output",
        str(PIP_AUDIT_FILE),
    ]

    scan = subprocess.run(
        scan_command,
        cwd=ROOT,
        capture_output=True,
        text=True,
    )

    detail = (
        scan.stdout
        + scan.stderr
    ).strip()

    if scan.returncode == 0:
        record(
            "security.pip-audit",
            "PASS",
            (
                f"pip-audit {PIP_AUDIT_VERSION} completed "
                "without reported known vulnerabilities."
            ),
        )
    else:
        record(
            "security.pip-audit",
            "FAIL",
            (
                detail[-4000:]
                if detail
                else (
                    "pip-audit reported vulnerabilities or "
                    "could not complete successfully."
                )
            ),
        )


# ==============================================================
# MAIN
# ==============================================================


def main() -> int:
    """Run all independent audit checks."""

    ROOT.chdir() if hasattr(ROOT, "chdir") else None

    audit_requirements()

    workflow_files = get_workflow_files()

    for workflow in workflow_files:
        text = read_text(workflow)
        rel = workflow.relative_to(ROOT).as_posix()

        audit_action_sha(
            workflow,
            text,
            rel,
        )

        audit_python_baseline(
            workflow,
            text,
            rel,
        )

        audit_write_permissions(
            workflow,
            text,
            rel,
        )

        audit_checkout_credentials(
            workflow,
            text,
            rel,
        )

        audit_remote_shell(
            workflow,
            text,
            rel,
        )

    audit_python_syntax()
    audit_dependencies()

    status = "PASS" if not failures else "FAIL"

    report = {
        "audit": "JAS-JESI Independent Repository Security Audit",
        "status": status,
        "master_version": "1.0",
        "python_baseline": EXPECTED_PYTHON,
        "methodology_changed": False,
        "failure_count": len(failures),
        "warning_count": len(warnings),
        "failures": failures,
        "warnings": warnings,
        "checks": results,
    }

    AUDIT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    REPORT_FILE.write_text(
        json.dumps(
            report,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    print("=" * 58)
    print("JAS-JESI INDEPENDENT REPOSITORY SECURITY AUDIT")
    print("=" * 58)
    print(f"Status:   {status}")
    print(f"Failures: {len(failures)}")
    print(f"Warnings: {len(warnings)}")
    print(f"Report:   {REPORT_FILE.relative_to(ROOT)}")
    print("-" * 58)

    for failure in failures:
        print(f"FAIL: {failure}")

    for warning in warnings:
        print(f"WARN: {warning}")

    print("=" * 58)

    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
