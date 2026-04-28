"""Generate sample JPG images for generators that have a reference SVG.

Usage:
    python scripts/gen_sample_images.py [GeneratorName ...]

If no names are given, regenerates all JPGs for generators that have an SVG
stored in their generator folder.

The output JPG is written in the generator folder (same stem, .jpg),
1200 px wide (project convention) with a white background.
A thumbnail (<stem>-thumb.jpg) is also written in the same directory.
Thumbnails for the web UI are NOT separately regenerated – run
scripts/gen_thumbnails.sh for legacy static/samples/ thumbnails.
"""

from __future__ import annotations

import inspect
import io
import pathlib
import sys

from PIL import Image
from reportlab.graphics import renderPM
from svglib.svglib import svg2rlg

ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import boxes.generators  # noqa: E402

TARGET_W = 1200
THUMB_W = 200


def _gen_paths(cls: type) -> tuple[pathlib.Path, pathlib.Path]:
    """Return (svg_path, jpg_path) for a generator class.

    Handles both the legacy flat layout (``xxx.py``) and the new
    per-generator folder layout where the source is ``xxx/__init__.py``.
    """
    gen_file = pathlib.Path(inspect.getfile(cls))
    if gen_file.name == "__init__.py":
        stem = gen_file.parent.name
        folder = gen_file.parent
    else:
        stem = gen_file.stem
        folder = gen_file.parent
    return folder / f"{stem}.svg", folder / f"{stem}.jpg"


def make_thumbnail(jpg_path: pathlib.Path) -> None:
    thumb_path = jpg_path.with_name(jpg_path.stem + "-thumb.jpg")
    img = Image.open(jpg_path)
    ratio = THUMB_W / img.width
    thumb = img.resize((THUMB_W, int(img.height * ratio)), Image.LANCZOS)
    thumb.save(str(thumb_path), "JPEG", quality=85)
    print(f"Written {thumb_path}  ({thumb.width}x{thumb.height})")


def svg_to_jpg(svg_path: pathlib.Path, jpg_path: pathlib.Path) -> None:
    drawing = svg2rlg(str(svg_path))
    if drawing is None:
        raise ValueError(f"Could not parse {svg_path}")

    scale = TARGET_W / drawing.width
    drawing.width *= scale
    drawing.height *= scale
    drawing.transform = (scale, 0, 0, scale, 0, 0)

    png_bytes = renderPM.drawToString(drawing, fmt="PNG")
    img = Image.open(io.BytesIO(png_bytes)).convert("RGB")

    # White background (SVG is transparent)
    bg = Image.new("RGB", img.size, (255, 255, 255))
    bg.paste(img)

    jpg_path.parent.mkdir(parents=True, exist_ok=True)
    bg.save(str(jpg_path), "JPEG", quality=90)
    print(f"Written {jpg_path}  ({img.width}x{img.height})")


def main() -> None:
    names: list[str] = sys.argv[1:]

    all_gens = boxes.generators.getAllBoxGenerators()
    by_class_name = {v.__name__: v for v in all_gens.values()}

    targets: list[tuple[pathlib.Path, pathlib.Path]] = []

    if names:
        for n in names:
            cls = by_class_name.get(n)
            if cls is None:
                print(f"SKIP  {n} (unknown generator)")
                continue
            targets.append(_gen_paths(cls))
    else:
        seen: set[str] = set()
        for cls in all_gens.values():
            if cls.__name__ in seen:
                continue
            seen.add(cls.__name__)
            svg, jpg = _gen_paths(cls)
            if svg.exists():
                targets.append((svg, jpg))

    for svg_path, jpg_path in sorted(targets):
        if not svg_path.exists():
            print(f"SKIP  {svg_path} (not found)")
            continue
        try:
            svg_to_jpg(svg_path, jpg_path)
            make_thumbnail(jpg_path)
        except Exception as exc:
            print(f"ERROR {svg_path}: {exc}")


if __name__ == "__main__":
    main()
