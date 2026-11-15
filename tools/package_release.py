#!/usr/bin/env python3
# encoding: utf-8
"""Pack the shared schema into one archive per frontend.

The version is the first heading in CHANGELOG.md. Each zip is flat:
Hamster rejects a wrapper directory, and Trime reads the user directory
the same way. Mobile archives leave out rime.lua and default.yaml.
Desktop archives include rime.lua and only that frontend's installer.
"""

from __future__ import annotations

import argparse
import re
import sys
import time
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"

SHARED = (
    "hanzi_tong.schema.yaml",
    "hanzi_tong.dict.yaml",
    "hanzi_tong.pinyin.dict.yaml",
    "hanzi_tong.jyutping.dict.yaml",
    "hanzi_tong.poj.dict.yaml",
    "hanzi_tong.hanja.dict.yaml",
    "hanzi_tong.kanji.dict.yaml",
    "lua/hanzi_tong.lua",
    "LICENSE",
    "NOTICE.md",
)

# arcname, path relative to the repository root.
# A repeated arcname is how a platform README becomes README.md in the zip.
PACKAGES = {
    "windows-weasel": (
        ("README.md", "platforms/windows/README.md"),
        ("rime.lua", "rime.lua"),
        ("tools/install-weasel.ps1", "tools/install-weasel.ps1"),
    ),
    "macos-squirrel": (
        ("README.md", "platforms/macos/README.md"),
        ("rime.lua", "rime.lua"),
        ("tools/install-squirrel.sh", "tools/install-squirrel.sh"),
        ("tools/install-rime-user.sh", "tools/install-rime-user.sh"),
    ),
    "linux-ibus-fcitx": (
        ("README.md", "platforms/linux/README.md"),
        ("rime.lua", "rime.lua"),
        ("tools/install-linux.sh", "tools/install-linux.sh"),
        ("tools/install-rime-user.sh", "tools/install-rime-user.sh"),
    ),
    "android-trime": (
        ("README.md", "platforms/android/README.md"),
        ("hanzi_tong.custom.yaml", "platforms/android/trime/hanzi_tong.custom.yaml"),
        ("hanzi_tong.default-patch.yaml", "platforms/android/trime/hanzi_tong.default-patch.yaml"),
        ("hanzi_tong.trime-patch.yaml", "platforms/android/trime/hanzi_tong.trime-patch.yaml"),
    ),
    "ios-hamster": (
        ("README.md", "platforms/ios/README.md"),
        ("hanzi_tong.custom.yaml", "platforms/ios/hamster/hanzi_tong.custom.yaml"),
        ("hanzi_tong.default-patch.yaml", "platforms/ios/hamster/hanzi_tong.default-patch.yaml"),
        ("hanzi_tong.keyboard.yaml", "platforms/ios/hamster/hanzi_tong.keyboard.yaml"),
    ),
}

# Names an import would use to replace an existing frontend setup.
# hanzi_tong.custom.yaml is intentionally not listed: the mobile schema
# needs that patch, and it only rewrites the filter list.
MOBILE_KINDS = frozenset({"android-trime", "ios-hamster"})
MOBILE_FORBIDDEN = frozenset(
    {
        "rime.lua",
        "default.yaml",
        "default.custom.yaml",
        "trime.yaml",
        "trime.custom.yaml",
        "hamster.yaml",
        "hamster.custom.yaml",
    }
)

_VERSION = re.compile(r"^## (\d+\.\d+\.\d+)\b", re.MULTILINE)


def read_version(root: Path | None = None) -> str:
    text = ((root or ROOT) / "CHANGELOG.md").read_text(encoding="utf-8")
    match = _VERSION.search(text)
    if not match:
        raise SystemExit("CHANGELOG.md has no ## x.y.z heading")
    return match.group(1)


def members(kind: str) -> list[tuple[str, str]]:
    if kind not in PACKAGES:
        known = ", ".join(PACKAGES)
        raise SystemExit(f"Unknown package '{kind}'. Use {known}.")
    shared = [(name, name) for name in SHARED]
    return shared + list(PACKAGES[kind])


def archive_name(version: str, kind: str) -> str:
    return f"hanzi-tong-{version}-{kind}.zip"


def missing_sources(root: Path, kind: str) -> list[str]:
    return [rel for _arc, rel in members(kind) if not (root / rel).is_file()]


def check_members(kind: str) -> None:
    names = [arc for arc, _rel in members(kind)]
    if len(names) != len(set(names)):
        raise SystemExit(f"{kind} repeats an archive path")
    for arc in names:
        parts = arc.split("/")
        if arc.startswith("/") or "\\" in arc or ".." in parts:
            raise SystemExit(f"{kind} has an unsafe path {arc}")
        if len(parts) > 1 and parts[0] not in {"lua", "tools"}:
            raise SystemExit(f"{kind} wraps files in {parts[0]}/")
    if "hanzi_tong.schema.yaml" not in names:
        raise SystemExit(f"{kind} is missing the schema at the archive root")
    if kind in MOBILE_KINDS:
        forbidden = sorted(set(names) & MOBILE_FORBIDDEN)
        if forbidden:
            raise SystemExit(f"{kind} would overwrite {', '.join(forbidden)}")


def write_package(root: Path, kind: str, dest_dir: Path, version: str | None = None) -> Path:
    check_members(kind)
    absent = missing_sources(root, kind)
    if absent:
        raise SystemExit("Missing " + ", ".join(absent) + ". Run tools/build_dictionaries.py first.")
    version = version or read_version(root)
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / archive_name(version, kind)
    with zipfile.ZipFile(dest, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for arcname, rel in members(kind):
            info = zipfile.ZipInfo(arcname)
            stamp = max((root / rel).stat().st_mtime, 315532800)
            info.date_time = time.localtime(stamp)[:6]
            info.flag_bits |= 0x800
            info.compress_type = zipfile.ZIP_DEFLATED
            data = (root / rel).read_bytes()
            archive.writestr(info, data)
    return dest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Pack 漢字通 release archives.")
    parser.add_argument(
        "kinds",
        nargs="*",
        default=list(PACKAGES),
        help="Package id. Default: every frontend.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Report missing files and write nothing.",
    )
    args = parser.parse_args(argv)
    version = read_version()
    failed = False
    for kind in args.kinds:
        check_members(kind)
        absent = missing_sources(ROOT, kind)
        name = archive_name(version, kind)
        if absent:
            failed = True
            print(f"{name}: missing {', '.join(absent)}", file=sys.stderr)
            continue
        if args.check:
            print(f"{name}: {len(members(kind))} files")
            continue
        path = write_package(ROOT, kind, DIST, version)
        print(path)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
