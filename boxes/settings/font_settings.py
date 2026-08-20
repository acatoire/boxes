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

"""FontSettings – reusable argparse group for font selection.

Usage in any generator::

    from boxes.fontsettings import FontSettings

    class MyGenerator(Boxes):
        def __init__(self) -> None:
            Boxes.__init__(self)
            self.addSettingsArgs(FontSettings)

        def render(self) -> None:
            ctx = cast(Context, self.ctx)
            ctx.set_font(self.Font_font,
                         bold=self.Font_bold,
                         italic=self.Font_italic)
            self.text("Hello", x=10, y=10,
                      fontsize=self.Font_size,
                      color=Color.ETCHING)

To draw :class:`~boxes.settings.text_settings.TextSettings`'s (possibly
multi-line, via a literal "\\n") text sized from a paired FontSettings group
in one call, use :func:`boxes.settings.text_settings.draw_text_block`
instead of calling ``self.text()`` directly.
"""

from __future__ import annotations

import argparse

from boxes import boolarg
from boxes.args import FloatStepper
from boxes.edges import Settings
from boxes.fontmanager import discover_fonts


class FontSettings(Settings):
    """Font Settings

    Controls the font used for engraved text.

     * size                : 4.0  : Primary font size [mm]
     * secondary_size_coef : 0.8  : Size of every line after the first, as a
                                    fraction of the primary size (for
                                    multi-line text entered via "\\n")
     * bold                : False : Bold font weight
     * italic              : False : Italic font style
    """

    # font is handled manually in parserArguments (dynamic choices).
    absolute_params: dict = {
        "size":                 4.0,
        "secondary_size_coef":  0.8,
        "bold":                 False,
        "italic":               False,
        "font_as_path":         True,
    }
    relative_params: dict = {}

    @classmethod
    def parserArguments(cls, parser: argparse.ArgumentParser,
                        prefix: str | None = None, **defaults: object) -> None:
        """Register arguments in a dedicated *Font Settings* group."""
        prefix = prefix or "Font"

        group = parser.add_argument_group("Font Settings")
        group.prefix = prefix  # type: ignore[attr-defined]

        available_fonts = discover_fonts()
        default_font = str(defaults.get("font", "sans-serif"))
        if default_font not in available_fonts:
            default_font = "sans-serif"

        group.add_argument(
            f"--{prefix}_font",
            action="store", type=str,
            default=default_font,
            choices=available_fonts,
            help="Font family for engraved text")

        default_size = float(defaults.get("size", cls.absolute_params["size"]))  # type: ignore[arg-type]
        group.add_argument(
            f"--{prefix}_size",
            action="store", type=FloatStepper(0.5),
            default=default_size,
            help="Primary font size [mm]")

        default_secondary_coef = float(
            defaults.get("secondary_size_coef", cls.absolute_params["secondary_size_coef"])  # type: ignore[arg-type]
        )
        group.add_argument(
            f"--{prefix}_secondary_size_coef",
            action="store", type=FloatStepper(0.05),
            default=default_secondary_coef,
            help="Size of every line after the first, as a fraction of the primary size "
                 '(for multi-line text entered via "\\n")')

        default_bold = bool(defaults.get("bold", cls.absolute_params["bold"]))
        group.add_argument(
            f"--{prefix}_bold",
            action="store", type=boolarg,
            default=default_bold,
            help="Bold font weight")

        default_italic = bool(defaults.get("italic", cls.absolute_params["italic"]))
        group.add_argument(
            f"--{prefix}_italic",
            action="store", type=boolarg,
            default=default_italic,
            help="Italic font style")

        default_as_path = bool(defaults.get("font_as_path", cls.absolute_params["font_as_path"]))
        group.add_argument(
            f"--{prefix}_font_as_path",
            action="store", type=boolarg,
            default=default_as_path,
            help="Convert text to paths for maximum laser-app compatibility")

    def __init__(self, thickness: float, relative: bool = True, **kw: object) -> None:
        # FontSettings has no relative params and needs no thickness scaling.
        self.values: dict = {}
        self.thickness = thickness
