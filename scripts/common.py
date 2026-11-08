"""Gate logging copied from hei_projects hei_scripts.gate.common (subset)."""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

DIVIDER = "─" * 60
SECTION_DIVIDER = "─" * 32
REPO_ROOT = Path(__file__).resolve().parents[1]


def log_ok(message: str) -> None:
    print(f"  ✅ {message}")


def log_fail(message: str) -> None:
    print(f"  ❌ {message}")


def log_warn(message: str) -> None:
    print(f"  ⚠️ {message}")


def log_info(message: str) -> None:
    print(f"  ℹ️ {message}")


class CheckResult:
    def __init__(self) -> None:
        self.failures = 0
        self.passed = 0

    def ok(self, message: str) -> None:
        log_ok(message)
        self.passed += 1

    def fail(self, message: str) -> None:
        log_fail(message)
        self.failures += 1


def print_section(title: str) -> None:
    print(f"🧪 {title}")
    print(SECTION_DIVIDER)


def print_banner(title: str, **fields: str) -> None:
    print(f"🧪 {title}")
    print(DIVIDER)
    for label, value in fields.items():
        print(f"  {label:<12}: {value}")
    print(DIVIDER)
    print("")


def print_result(result: CheckResult, *, pass_message: str) -> int:
    print(DIVIDER)
    if result.failures == 0:
        print(f"✅ Result: PASS ({pass_message})")
        return 0
    print(f"❌ Result: FAIL ({result.failures} check(s) failed)")
    return 1


def run_cmd(cmd: list[str], *, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    resolved = list(cmd)
    exe = shutil.which(resolved[0])
    if exe:
        resolved[0] = exe
    return subprocess.run(
        resolved,
        cwd=str(cwd or REPO_ROOT),
        capture_output=True,
        text=True,
    )
