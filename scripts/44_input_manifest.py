#!/usr/bin/env python3
"""Create and verify SHA-256 manifests for frozen JESI input files."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
CHUNK_SIZE = 1024 * 1024


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(CHUNK_SIZE), b""):
            digest.update(chunk)
    return digest.hexdigest()


def repo_relative(path: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(ROOT.resolve()).as_posix()
    except ValueError as exc:
        raise ValueError(
            f"Input must be inside the repository: {path}"
        ) from exc


def collect_files(extra_files: list[str]) -> list[Path]:
    if not RAW_DIR.is_dir():
        raise FileNotFoundError(f"Missing raw-data directory: {RAW_DIR}")

    files: set[Path] = set()

    for path in RAW_DIR.rglob("*"):
        if path.is_symlink():
            raise ValueError(f"Symlink inputs are not supported: {path}")
        if path.is_file():
            files.add(path)

    for item in extra_files:
        candidate = ROOT / item
        if candidate.is_symlink():
            raise ValueError(f"Symlink inputs are not supported: {candidate}")

        path = candidate.resolve()
        if not path.is_file():
            raise FileNotFoundError(f"Missing extra input: {item}")

        repo_relative(path)
        files.add(path)

    return sorted(files, key=repo_relative)


def build_manifest(extra_files: list[str]) -> dict:
    entries = []

    for path in collect_files(extra_files):
        entries.append(
            {
                "path": repo_relative(path),
                "size_bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
        )

    return {
        "manifest_version": 1,
        "algorithm": "sha256",
        "file_count": len(entries),
        "files": entries,
    }


def create_manifest(output: str, extra_files: list[str]) -> None:
    manifest = build_manifest(extra_files)
    output_path = (ROOT / output).resolve()
    repo_relative(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"Manifest created: {repo_relative(output_path)}")
    print(f"Files recorded: {manifest['file_count']}")


def verify_manifest(manifest_name: str, extra_files: list[str]) -> None:
    manifest_path = (ROOT / manifest_name).resolve()
    expected = json.loads(manifest_path.read_text(encoding="utf-8"))
    actual = build_manifest(extra_files)

    if expected.get("algorithm") != "sha256":
        raise ValueError("Unsupported manifest algorithm.")

    expected_files = {
        item["path"]: item for item in expected.get("files", [])
    }
    actual_files = {
        item["path"]: item for item in actual["files"]
    }

    missing = sorted(set(expected_files) - set(actual_files))
    unexpected = sorted(set(actual_files) - set(expected_files))
    changed = sorted(
        path
        for path in set(expected_files) & set(actual_files)
        if (
            expected_files[path].get("sha256")
            != actual_files[path].get("sha256")
            or expected_files[path].get("size_bytes")
            != actual_files[path].get("size_bytes")
        )
    )

    if missing or unexpected or changed:
        print("INPUT MANIFEST VERIFICATION: FAILED")
        if missing:
            print("Missing files:", ", ".join(missing))
        if unexpected:
            print("Unexpected files:", ", ".join(unexpected))
        if changed:
            print("Changed files:", ", ".join(changed))
        raise SystemExit(1)

    if expected.get("file_count") != len(expected_files):
        raise ValueError("Manifest file_count does not match its entries.")

    print("INPUT MANIFEST VERIFICATION: PASSED")
    print(f"Files verified: {len(actual_files)}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create or verify a SHA-256 input manifest."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    create = subparsers.add_parser("create")
    create.add_argument("--output", required=True)
    create.add_argument(
        "--extra-file",
        action="append",
        default=[],
        help="Additional repository-relative input; repeat if needed.",
    )

    verify = subparsers.add_parser("verify")
    verify.add_argument("--manifest", required=True)
    verify.add_argument(
        "--extra-file",
        action="append",
        default=[],
        help="Additional repository-relative input; repeat if needed.",
    )

    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        if args.command == "create":
            create_manifest(args.output, args.extra_file)
        else:
            verify_manifest(args.manifest, args.extra_file)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
