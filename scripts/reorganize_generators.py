# Copyright (C) 2026 boxes-acatoire contributors
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""reorganize_generators.py – one-time migration script.

Moves every flat ``xxx.py`` (plus its associated ``xxx.svg``, ``xxx.jpg``,
``xxx-thumb.jpg`` and hashed ``xxx_<hash>.svg`` files) into a dedicated
``xxx/`` sub-folder, renaming the Python source to ``__init__.py``.

BEFORE::

    boxes/generators/boxes/abox.py
    boxes/generators/boxes/abox.svg
    boxes/generators/boxes/abox.jpg
    boxes/generators/boxes/abox-thumb.jpg

AFTER::

    boxes/generators/boxes/abox/__init__.py
    boxes/generators/boxes/abox/abox.svg
    boxes/generators/boxes/abox/abox.jpg
    boxes/generators/boxes/abox/abox-thumb.jpg

Run from the repository root::

    python scripts/reorganize_generators.py [--dry-run]

Pass ``--dry-run`` to preview what would be moved without touching anything.
"""

from __future__ import annotations

import argparse
import shutil
pass
from pathlib import Path

GENERATORS_ROOT = Path(__file__).resolve().parent.parent / "boxes" / "generators"

# Category sub-directories (all direct children that are packages)
CATEGORY_DIRS = [
    p for p in GENERATORS_ROOT.iterdir()
    if p.is_dir() and not p.name.startswith("_") and not p.name.startswith(".")
]


def migrate_category(category_dir: Path, dry_run: bool) -> int:
    """Migrate all generators in *category_dir*. Returns number of generators moved."""
    moved = 0
    for py_file in sorted(category_dir.glob("*.py")):
        stem = py_file.stem
        if stem.startswith("_"):
            continue  # skip __init__.py, _helpers, …

        dest_dir = category_dir / stem
        if dest_dir.exists():
            print(f"  SKIP  {py_file.relative_to(GENERATORS_ROOT)}  (dest exists)")
            continue

        # Collect files to move: py + svg + jpg + thumb + hashed svgs
        files_to_move: list[tuple[Path, Path]] = [
            (py_file, dest_dir / "__init__.py"),
        ]
        for suffix in (".svg", ".jpg"):
            src = py_file.with_suffix(suffix)
            if src.exists():
                files_to_move.append((src, dest_dir / (stem + suffix)))
        thumb = category_dir / f"{stem}-thumb.jpg"
        if thumb.exists():
            files_to_move.append((thumb, dest_dir / f"{stem}-thumb.jpg"))
        for hashed_svg in sorted(category_dir.glob(f"{stem}_????????.svg")):
            files_to_move.append((hashed_svg, dest_dir / hashed_svg.name))

        print(f"  {'[DRY]' if dry_run else 'MOVE'} {py_file.relative_to(GENERATORS_ROOT)}"
              f" -> {dest_dir.relative_to(GENERATORS_ROOT)}/")
        for src, dst in files_to_move:
            print(f"         {src.name} -> {dst.relative_to(category_dir)}")

        if not dry_run:
            dest_dir.mkdir()
            for src, dst in files_to_move:
                shutil.move(str(src), str(dst))

        moved += 1

    return moved


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dry-run", action="store_true",
                        help="Preview without making any changes.")
    args = parser.parse_args()

    if args.dry_run:
        print("=== DRY RUN – no files will be touched ===\n")

    total = 0
    for cat in sorted(CATEGORY_DIRS):
        print(f"\n[{cat.name}]")
        total += migrate_category(cat, args.dry_run)

    print(f"\n{'Would move' if args.dry_run else 'Moved'} {total} generator(s).")
    if args.dry_run:
        print("Re-run without --dry-run to apply.")


if __name__ == "__main__":
    main()
