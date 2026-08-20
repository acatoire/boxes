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

"""TextSettings – reusable argparse group for engraved text on laser-cut parts.

Usage in any generator::

    from boxes.settings.text_settings import TextSettings

    class MyGenerator(Boxes):
        # mypy stubs
        Text_text:    str   = "Label"
        Text_align:   str   = "middle center"  # see TextSettings.ALIGN_CHOICES
        Text_x:       float = 0.0   # X offset from centre [mm]
        Text_y:       float = 0.0   # Y offset from centre [mm]
        Text_step:    float = 1.0   # d-pad step (UI only)
        Text_outline: float = 0.0   # outside outline stroke width [mm]

        def __init__(self) -> None:
            Boxes.__init__(self)
            self.addSettingsArgs(TextSettings)

        def render(self) -> None:
            cx, cy = ..., ...
            self.text(self.Text_text,
                      x=cx + self.Text_x, y=cy + self.Text_y,
                      align=self.Text_align,
                      fontsize=self.Font_size,
                      color=Color.ETCHING,
                      outline_lw=self.Text_outline)
"""

from __future__ import annotations

import argparse

from boxes.args import DPadMoverArg, FloatStepper
from boxes.Color import Color
from boxes.edges import Settings

# Minimal gap between stacked lines, as a fraction of the primary font size.
_LINE_GAP_FRACTION = 0.15


def measure_text_block(boxes_obj, text_prefix: str = "Text", font_prefix: str = "Font",
                        text_override: str | None = None) -> tuple[list[str], list[float], float, float]:
    """Return ``(lines, sizes, gap, total_height)`` for *text_prefix*'s
    (possibly multi-line, via a literal ``"\\n"``) text, sized from
    *font_prefix*'s :class:`~boxes.settings.font_settings.FontSettings` --
    the first line at the primary size, every line after at
    ``primary * {font_prefix}_secondary_size_coef``.

    Pass *text_override* to size different text than what's actually in
    ``{text_prefix}_text`` (e.g. an auto-generated caption).

    Returns ``([], [], 0.0, 0.0)`` if there is nothing to draw (empty text
    or a zero/negative primary size)."""
    raw = text_override if text_override is not None else getattr(boxes_obj, f"{text_prefix}_text", "")
    text = (raw or "").replace("\\n", "\n")
    lines = text.split("\n") if text else []
    primary = getattr(boxes_obj, f"{font_prefix}_size", 0.0)
    if not lines or primary <= 0:
        return [], [], 0.0, 0.0
    coef = getattr(boxes_obj, f"{font_prefix}_secondary_size_coef", 1.0)
    sizes = [primary if i == 0 else primary * coef for i in range(len(lines))]
    gap = _LINE_GAP_FRACTION * primary
    total_height = sum(sizes) + gap * (len(lines) - 1)
    return lines, sizes, gap, total_height


def draw_text_block(boxes_obj, cx: float, cy: float, text_prefix: str = "Text", font_prefix: str = "Font",
                     color=None, text_override: str | None = None, valign_override: str | None = None) -> float:
    """Draw *text_prefix*'s text (see :func:`measure_text_block`) anchored at
    ``(cx + {prefix}_x, cy + {prefix}_y)`` per ``{prefix}_align`` (one of
    :attr:`TextSettings.ALIGN_CHOICES`), using *font_prefix*'s font.

    *valign_override* forces the vertical half of the alignment (still
    reading the horizontal half from ``{prefix}_align``) -- for callers that
    reserve a block exactly ``total_height`` tall (so the block's placement
    within it isn't a free choice), e.g. always ``"bottom"`` to grow the
    block upward from *cy*.

    Returns the total block height drawn (0.0 if there was nothing to draw)."""
    lines, sizes, gap, total_height = measure_text_block(boxes_obj, text_prefix, font_prefix, text_override)
    if not lines:
        return 0.0

    align = getattr(boxes_obj, f"{text_prefix}_align", "middle center")
    valign, _, halign = align.partition(" ")
    if valign_override is not None:
        valign = valign_override
    halign = halign or "center"

    if valign == "top":
        top = cy
    elif valign == "bottom":
        top = cy + total_height
    else:
        top = cy + total_height / 2
    top += getattr(boxes_obj, f"{text_prefix}_y", 0.0)
    x = cx + getattr(boxes_obj, f"{text_prefix}_x", 0.0)

    boxes_obj.ctx.set_font(
        getattr(boxes_obj, f"{font_prefix}_font", "sans-serif"),
        bold=getattr(boxes_obj, f"{font_prefix}_bold", False),
        italic=getattr(boxes_obj, f"{font_prefix}_italic", False),
        as_path=getattr(boxes_obj, f"{font_prefix}_font_as_path", True),
    )
    outline = getattr(boxes_obj, f"{text_prefix}_outline", 0.0)
    text_color = color if color is not None else Color.ETCHING
    for line, size in zip(lines, sizes):
        boxes_obj.text(line, x=x, y=top, align=f"top {halign}",
                        fontsize=size, color=text_color, outline_lw=outline)
        top -= size + gap
    return total_height


class TextSettings(Settings):
    """Text Settings

    Controls the text content and position for laser-engraved text.

     * text    : Label         : Text to engrave (leave blank to omit)
     * align   : middle center : Text alignment relative to (x, y)
     * x       : 0.0           : Text X offset from centre [mm]
     * y       : 0.0           : Text Y offset from centre [mm]
     * step    : 1.0           : D-pad movement step [mm]
     * outline : 0.0           : Outside stroke width around each glyph [mm] (0 = none)
    """

    ALIGN_CHOICES = [
        "top left", "top center", "top right",
        "middle left", "middle center", "middle right",
        "bottom left", "bottom center", "bottom right",
    ]

    absolute_params: dict = {
        "text":    "Label",
        "align":   "middle center",
        "x":       0.0,
        "y":       0.0,
        "step":    1.0,
        "outline": 0.0,
    }
    relative_params: dict = {}

    @classmethod
    def parserArguments(
        cls,
        parser: argparse.ArgumentParser,
        prefix: str | None = None,
        **defaults: object,
    ) -> None:
        """Register all text arguments in a dedicated *Text Settings* group."""
        prefix = prefix or "Text"

        group = parser.add_argument_group("Text Settings")
        group.prefix = prefix  # type: ignore[attr-defined]

        group.add_argument(
            f"--{prefix}_text",
            action="store", type=str,
            default=str(defaults.get("text", cls.absolute_params["text"])),
            help="Text to engrave on the label (leave blank to omit)")

        default_align = str(defaults.get("align", cls.absolute_params["align"]))
        if default_align not in cls.ALIGN_CHOICES:
            default_align = cls.absolute_params["align"]
        group.add_argument(
            f"--{prefix}_align",
            action="store", type=str,
            default=default_align,
            choices=cls.ALIGN_CHOICES,
            help="Text alignment relative to the given (x, y) position")

        x_field = f"{prefix}_x"
        y_field = f"{prefix}_y"

        group.add_argument(
            f"--{x_field}",
            action="store", type=FloatStepper(1.0),
            default=float(defaults.get("x", cls.absolute_params["x"])),  # type: ignore[arg-type]
            help="Text X offset from centre [mm]")

        group.add_argument(
            f"--{y_field}",
            action="store", type=FloatStepper(1.0),
            default=float(defaults.get("y", cls.absolute_params["y"])),  # type: ignore[arg-type]
            help="Text Y offset from centre [mm]")

        group.add_argument(
            f"--{prefix}_step",
            action="store", type=DPadMoverArg(x_field, y_field, step=0.5),
            default=float(defaults.get("step", cls.absolute_params["step"])),  # type: ignore[arg-type]
            help="D-pad: click arrows to move text, · to re-centre")

        group.add_argument(
            f"--{prefix}_outline",
            action="store", type=FloatStepper(0.1),
            default=float(defaults.get("outline", cls.absolute_params["outline"])),  # type: ignore[arg-type]
            help="Outside stroke width around each glyph [mm] (0 = no outline)")

    def __init__(self, thickness: float, relative: bool = True, **kw: object) -> None:
        # No relative params; thickness stored for API compatibility only.
        self.values: dict = {}
        self.thickness = thickness
