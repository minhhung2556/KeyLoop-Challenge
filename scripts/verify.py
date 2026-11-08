"""Local verification gate. hei_projects CheckResult style."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from common import CheckResult, REPO_ROOT, print_banner, print_result, print_section, run_cmd


def check_backend(result: CheckResult) -> None:
    print_section("backend pytest")
    python = sys.executable
    proc = run_cmd(
        [python, "-m", "pytest", "backend/tests", "-q", "--tb=short"],
        cwd=REPO_ROOT,
    )
    if proc.returncode == 0:
        result.ok("pytest backend/tests")
    else:
        result.fail("pytest failed")
        if proc.stdout:
            print(proc.stdout[-2000:])
        if proc.stderr:
            print(proc.stderr[-2000:])


def check_frontend(result: CheckResult) -> None:
    print_section("frontend typecheck + tests")
    npm = "npm"
    typecheck = run_cmd([npm, "run", "typecheck"], cwd=REPO_ROOT / "frontend")
    if typecheck.returncode == 0:
        result.ok("npm run typecheck")
    else:
        result.fail("typecheck failed")
        print((typecheck.stdout + typecheck.stderr)[-2000:])
    tests = run_cmd([npm, "test"], cwd=REPO_ROOT / "frontend")
    if tests.returncode == 0:
        result.ok("npm test")
    else:
        result.fail("npm test failed")
        print((tests.stdout + tests.stderr)[-2000:])


def check_video(result: CheckResult) -> None:
    print_section("walkthrough mp4")
    mp4 = REPO_ROOT / "video/output/keyloop_walkthrough.mp4"
    if mp4.is_file() and mp4.stat().st_size > 0:
        result.ok(f"{mp4.relative_to(REPO_ROOT)} ({mp4.stat().st_size} bytes)")
    else:
        result.fail("video/output/keyloop_walkthrough.mp4 missing or empty")


def check_step(step: str, result: CheckResult) -> None:
    print_section(f"step {step}")
    mapping = {
        "phase1-scaffold-backend": [
            REPO_ROOT / "backend/app/config.py",
            REPO_ROOT / "backend/app/utils/async_io.py",
            REPO_ROOT / "backend/app/middleware/request_id.py",
        ],
        "phase2-backend-data": [
            REPO_ROOT / "backend/app/schemas/lead.py",
            REPO_ROOT / "backend/app/repositories/lead_repository.py",
            REPO_ROOT / "backend/app/seed.py",
        ],
        "phase2-backend-api": [
            REPO_ROOT / "backend/app/services/lead_service.py",
            REPO_ROOT / "backend/app/api/v1/leads.py",
            REPO_ROOT / "backend/app/main.py",
        ],
    }
    paths = mapping.get(step)
    if not paths:
        result.ok(f"no file checklist for {step}")
        return
    for path in paths:
        if path.is_file():
            result.ok(str(path.relative_to(REPO_ROOT)))
        else:
            result.fail(f"missing {path.relative_to(REPO_ROOT)}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--step", default=None)
    parser.add_argument("--backend", action="store_true")
    parser.add_argument("--frontend", action="store_true")
    parser.add_argument("--video", action="store_true")
    parser.add_argument("--all", action="store_true")
    args = parser.parse_args()
    if not any([args.step, args.backend, args.frontend, args.video, args.all]):
        parser.print_help()
        return 0
    print_banner("verify", mode=args.step or ("all" if args.all else "layer"))
    result = CheckResult()
    if args.step:
        check_step(args.step, result)
    if args.backend or args.all:
        check_backend(result)
    if args.frontend or args.all:
        check_frontend(result)
    if args.video or args.all:
        check_video(result)
    return print_result(result, pass_message="verify complete")


if __name__ == "__main__":
    raise SystemExit(main())
