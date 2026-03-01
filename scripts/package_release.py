from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path
import zipfile


INTEGRATION_ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Package ShelfShare Home Assistant integration as a zip artifact."
    )
    parser.add_argument(
        "--version",
        default="dev",
        help="Version label for output filename (default: dev)",
    )
    parser.add_argument(
        "--output-dir",
        default=str(INTEGRATION_ROOT / "dist"),
        help="Directory to place generated zip file",
    )
    return parser.parse_args()


def build_file_list(root: Path) -> list[Path]:
    included_files: list[Path] = []

    for path in root.rglob("*"):
        if path.is_dir():
            continue

        relative = path.relative_to(root)
        if relative.parts[0] in {"dist", ".git", "__pycache__"}:
            continue

        if path.suffix in {".pyc", ".pyo"}:
            continue

        included_files.append(path)

    return sorted(included_files)


def create_archive(version: str, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)

    safe_version = version.replace("/", "-").replace(" ", "-")
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    archive_name = f"shelfshare-ha-{safe_version}-{timestamp}.zip"
    archive_path = output_dir / archive_name

    file_list = build_file_list(INTEGRATION_ROOT)

    with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in file_list:
            rel = path.relative_to(INTEGRATION_ROOT)
            archive.write(path, rel.as_posix())

    return archive_path


def main() -> None:
    args = parse_args()
    output_dir = Path(args.output_dir).resolve()
    archive_path = create_archive(args.version, output_dir)
    print(f"Created: {archive_path}")


if __name__ == "__main__":
    main()
