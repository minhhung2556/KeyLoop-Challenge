"""Copy reusable files from hei_projects and tiktok_creator. Local paths only."""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

from common import CheckResult, REPO_ROOT, print_banner, print_result, print_section

HEI = Path(r"E:\projects\hooemi\hei_projects")
TIKTOK = Path(r"E:\projects\tiktok_creator")


def copy_file(src: Path, dest: Path, result: CheckResult) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if not src.is_file():
        result.fail(f"missing source {src}")
        return
    shutil.copy2(src, dest)
    result.ok(f"{dest.relative_to(REPO_ROOT)}")


def patch_accent(css_path: Path) -> None:
    text = css_path.read_text(encoding="utf-8")
    text = text.replace("#EC5800", "#00b5d8")
    text = text.replace("rgba(236, 88, 0", "rgba(0, 181, 216")
    if ".bg-blue-20" not in text:
        text += """

.bg-blue-20 {
  --tw-bg-opacity: 1;
  background-color: rgba(0, 181, 216, var(--tw-bg-opacity));
}
"""
    css_path.write_text(text, encoding="utf-8")


def bootstrap_backend(result: CheckResult, dry_run: bool) -> None:
    print_section("backend")
    pairs = [
        (HEI / "hei_backend/app/middleware/request_id.py", REPO_ROOT / "backend/app/middleware/request_id.py"),
        (HEI / "hei_backend/app/middleware/logging.py", REPO_ROOT / "backend/app/middleware/logging.py"),
        (HEI / "hei_backend/app/utils/errors.py", REPO_ROOT / "backend/app/utils/errors.py"),
    ]
    for src, dest in pairs:
        if dry_run:
            result.ok(f"dry-run {dest.relative_to(REPO_ROOT)}")
            continue
        copy_file(src, dest, result)


def bootstrap_frontend(result: CheckResult, dry_run: bool) -> None:
    print_section("frontend")
    pairs = [
        (HEI / "hei_frontend/src/styles/theme.css", REPO_ROOT / "frontend/src/styles/theme.css"),
        (HEI / "hei_frontend/src/styles/globals.css", REPO_ROOT / "frontend/src/styles/globals.css"),
        (HEI / "hei_frontend/src/components/dashboard/dashboardStyles.js", REPO_ROOT / "frontend/src/components/dashboard/dashboardStyles.ts"),
        (HEI / "hei_frontend/src/utils/leadAttribution.ts", REPO_ROOT / "frontend/src/utils/leadAttribution.ts"),
        (HEI / "hei_frontend/scripts/log-style.js", REPO_ROOT / "frontend/scripts/log-style.js"),
        (HEI / "hei_frontend/scripts/emoji-test-reporter.mjs", REPO_ROOT / "frontend/scripts/emoji-test-reporter.mjs"),
    ]
    for src, dest in pairs:
        if dry_run:
            result.ok(f"dry-run {dest.relative_to(REPO_ROOT)}")
            continue
        copy_file(src, dest, result)
        if dest.name in {"theme.css", "dashboardStyles.ts"}:
            patch_accent(dest)


def bootstrap_video(result: CheckResult, dry_run: bool) -> None:
    print_section("video assets")
    src_root = TIKTOK / "assets/templates/composition"
    dest_root = REPO_ROOT / "video/assets"
    files = [
        src_root / "vendor/gsap.min.js",
        src_root / "fonts.css",
    ]
    font_dir = src_root / "fonts"
    if dry_run:
        result.ok("dry-run video/assets")
        return
    for src in files:
        copy_file(src, dest_root / src.name if src.name != "gsap.min.js" else dest_root / "vendor/gsap.min.js", result)
    if font_dir.is_dir():
        for font in font_dir.glob("*"):
            if font.is_file():
                copy_file(font, dest_root / "fonts" / font.name, result)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", choices=["backend", "frontend", "video", "all"], default="all")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    print_banner("bootstrap_from_hei", target=args.target, dry_run=str(args.dry_run))
    result = CheckResult()
    if args.target in ("backend", "all"):
        bootstrap_backend(result, args.dry_run)
    if args.target in ("frontend", "all"):
        bootstrap_frontend(result, args.dry_run)
    if args.target in ("video", "all"):
        bootstrap_video(result, args.dry_run)
    return print_result(result, pass_message="bootstrap complete")


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    raise SystemExit(main())
