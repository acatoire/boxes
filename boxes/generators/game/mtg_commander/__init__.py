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

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import cast

from boxes import *
from boxes.args import FloatStepper
from boxes.drawing import Context
from boxes.settings.crenel_settings import CrenelSettings
from boxes.settings.font_settings import FontSettings
from boxes.settings.score_settings import ScoreSettings


def _resolve(value: float | None, auto: float, board_size: float) -> float:
    """Return the resolved coordinate.

    * ``None``     → use the auto-computed value.
    * negative     → measured from the far edge  (``board_size + value``).
    * non-negative → used as-is (distance from the near edge).
    """
    if value is None:
        return auto
    return board_size + value if value < 0 else value


@dataclass
class _WheelCfg:
    """Resolved configuration for one wheel group."""
    outer_diameter: float
    score_min: int
    score_max: int
    score_radius: float | None
    score_angle: float
    crenel_enabled: bool
    crenel_depth: float
    crenel_width: float
    crenel_shape: str
    crenel_rounded: bool
    crenel_radius: float
    font_size: float
    font_font: str
    font_bold: bool
    font_italic: bool
    font_font_as_path: bool


class MtgCommanderZone(Boxes):
    """MTG Commander Zone – board with 6 score wheels and a commander card slot"""

    ui_group = "Game"
    tags = ["unstable", "tcg", "mtg"]

    description = """
A laser-cut MTG Commander Zone tracker with **six independent score wheels** and
a **commander card slot**.

**Wheel groups**

* **3 × commander damage wheels** (default 0–20) – track commander damage dealt to each opponent.
* **2 × life wheels** (default 0–10) – track life totals.
* **1 × tax wheel** (default 0–5) – track the commander tax (extra cost each casting).

**Cut pieces**

* **Board** – rectangular base with six magnet pockets and a card-slot cutout.
* **Rings** (×6) – one spinning ring per wheel, engraved with score numbers.

**Assembly**

1. Press a magnet into each pocket on the board.
2. Drop each ring onto its magnet pocket; it spins freely.
3. Slide your commander card into the card slot.
"""

    # ------------------------------------------------------------------ #
    # mypy stubs – overwritten by argparse at runtime                      #
    # ------------------------------------------------------------------ #
    commander_outer_diameter: float = 45.0
    commander_vertical: bool = True
    life_outer_diameter: float = 35.0
    life_vertical: bool = False
    tax_outer_diameter: float = 25.0

    board_margin: float = 6.0
    wheel_spacing: float = 4.0
    row_spacing: float = 5.0
    magnet_diameter: float = 5.0

    card_width: float = 63.0
    card_height: float = 88.0
    card_slot_margin: float = 2.0

    # font – commander damage wheels
    font_commander_size: float = 4.0
    font_commander_font: str = "sans-serif"
    font_commander_bold: bool = False
    font_commander_italic: bool = False
    font_commander_font_as_path: bool = True

    # font – life wheels
    font_life_size: float = 5.5
    font_life_font: str = "sans-serif"
    font_life_bold: bool = False
    font_life_italic: bool = False
    font_life_font_as_path: bool = True

    # font – tax wheel
    font_tax_size: float = 4.0
    font_tax_font: str = "sans-serif"
    font_tax_bold: bool = False
    font_tax_italic: bool = False
    font_tax_font_as_path: bool = True

    # score – commander damage wheels
    score_commander_min: int = 0
    score_commander_max: int = 17
    score_commander_radius: float | None = None
    score_commander_angle: float = -90.0

    # score – life wheels
    score_life_min: int = 0
    score_life_max: int = 10
    score_life_radius: float | None = None
    score_life_angle: float = -90.0

    # score – tax wheel
    score_tax_min: int = 0
    score_tax_max: int = 5
    score_tax_radius: float | None = None
    score_tax_angle: float = -90.0

    # crenel (shared across all wheels)
    crenel_enabled: bool = True
    crenel_depth: float = 3.0
    crenel_width: float = 0.3
    crenel_shape: str = "radial"
    crenel_rounded: bool = True
    crenel_radius: float = 0.0

    # explicit board size (None = auto-fit content + margin)
    board_width: float | None = 120.0
    board_height: float | None = 150.0

    # explicit element positions on the board, from top-left (None = auto)
    # commander_x / commander_y : centre of the 3-commander-wheel row bounding box
    # life_x / life_y           : centre of the 2-life-wheel bounding box
    # tax_x / tax_y             : centre of the tax wheel
    # card_x / card_y           : top-left corner of the card-slot cutout
    commander_x: float | None = 20.0
    commander_y: float | None = 70.0
    life_x: float | None = 80.0
    life_y: float | None = -10.0
    tax_x: float | None = -35.0
    tax_y: float | None = 20.0
    card_x: float | None = 55.0
    card_y: float | None = 30.0

    def __init__(self) -> None:
        Boxes.__init__(self)

        self.addSettingsArgs(FontSettings, prefix="font_commander",
                             title="Font Commander Damage Wheels Settings",
                             size=self.font_commander_size, font=self.font_commander_font,
                             bold=self.font_commander_bold, italic=self.font_commander_italic)
        self.addSettingsArgs(FontSettings, prefix="font_life",
                             title="Font Life Wheels Settings",
                             size=self.font_life_size, font=self.font_life_font,
                             bold=self.font_life_bold, italic=self.font_life_italic)
        self.addSettingsArgs(FontSettings, prefix="font_tax",
                             title="Font Tax Wheel Settings",
                             size=self.font_tax_size, font=self.font_tax_font,
                             bold=self.font_tax_bold, italic=self.font_tax_italic)
        self.addSettingsArgs(ScoreSettings, prefix="score_commander",
                             title="Score Commander Damage Wheels Settings",
                             min=self.score_commander_min, max=self.score_commander_max,
                             radius=self.score_commander_radius, angle=self.score_commander_angle)
        self.addSettingsArgs(ScoreSettings, prefix="score_life",
                             title="Score Life Wheels Settings",
                             min=self.score_life_min, max=self.score_life_max,
                             radius=self.score_life_radius, angle=self.score_life_angle)
        self.addSettingsArgs(ScoreSettings, prefix="score_tax",
                             title="Score Tax Wheel Settings",
                             min=self.score_tax_min, max=self.score_tax_max,
                             radius=self.score_tax_radius, angle=self.score_tax_angle)
        self.addSettingsArgs(CrenelSettings, prefix="crenel",
                             enabled=self.crenel_enabled, depth=self.crenel_depth,
                             width=self.crenel_width, shape=self.crenel_shape,
                             rounded=self.crenel_rounded, radius=self.crenel_radius)

        self.argparser.add_argument(
            "--commander_outer_diameter", action="store", type=FloatStepper(1.0),
            default=self.commander_outer_diameter,
            help="Outer diameter of the commander damage wheels [mm]")
        self.argparser.add_argument(
            "--commander_vertical", action="store", type=boolarg,
            default=self.commander_vertical,
            help="Stack commander damage wheels vertically instead of horizontally")
        self.argparser.add_argument(
            "--life_outer_diameter", action="store", type=FloatStepper(1.0),
            default=self.life_outer_diameter,
            help="Outer diameter of the life wheels [mm]")
        self.argparser.add_argument(
            "--life_vertical", action="store", type=boolarg,
            default=self.life_vertical,
            help="Stack life wheels vertically instead of horizontally")
        self.argparser.add_argument(
            "--tax_outer_diameter", action="store", type=FloatStepper(1.0),
            default=self.tax_outer_diameter,
            help="Outer diameter of the tax wheel [mm]")
        self.argparser.add_argument(
            "--board_margin", action="store", type=FloatStepper(0.5),
            default=self.board_margin,
            help="Margin between wheel centres and board edge [mm]")
        self.argparser.add_argument(
            "--wheel_spacing", action="store", type=FloatStepper(0.5),
            default=self.wheel_spacing,
            help="Gap between adjacent wheel edges in the same row [mm]")
        self.argparser.add_argument(
            "--row_spacing", action="store", type=FloatStepper(0.5),
            default=self.row_spacing,
            help="Gap between wheel rows [mm]")
        self.argparser.add_argument(
            "--magnet_diameter", action="store", type=FloatStepper(0.1),
            default=self.magnet_diameter,
            help="Diameter of central magnet hole (0 = no hole) [mm]")
        self.argparser.add_argument(
            "--card_width", action="store", type=FloatStepper(0.5),
            default=self.card_width,
            help="Width of the commander card [mm]")
        self.argparser.add_argument(
            "--card_height", action="store", type=FloatStepper(0.5),
            default=self.card_height,
            help="Height of the commander card [mm]")
        self.argparser.add_argument(
            "--card_slot_margin", action="store", type=FloatStepper(0.1),
            default=self.card_slot_margin,
            help="Clearance added around the card in the slot [mm]")
        self.argparser.add_argument(
            "--board_width", action="store", type=FloatStepper(0.5, auto=True),
            default=self.board_width,
            help="Board width [mm]. auto = fit content + margin")
        self.argparser.add_argument(
            "--board_height", action="store", type=FloatStepper(0.5, auto=True),
            default=self.board_height,
            help="Board height [mm]. auto = fit content + margin")
        self.argparser.add_argument(
            "--commander_x", action="store", type=FloatStepper(0.5, auto=True),
            default=self.commander_x,
            help="X centre of commander-damage-wheels row [mm]. auto = centred")
        self.argparser.add_argument(
            "--commander_y", action="store", type=FloatStepper(0.5, auto=True),
            default=self.commander_y,
            help="Y centre of commander-damage-wheels row [mm]. auto = top row")
        self.argparser.add_argument(
            "--life_x", action="store", type=FloatStepper(0.5, auto=True),
            default=self.life_x,
            help="X centre of life-wheels row [mm]. auto = left side of second row")
        self.argparser.add_argument(
            "--life_y", action="store", type=FloatStepper(0.5, auto=True),
            default=self.life_y,
            help="Y centre of life-wheels row [mm]. auto = second row")
        self.argparser.add_argument(
            "--tax_x", action="store", type=FloatStepper(0.5, auto=True),
            default=self.tax_x,
            help="X centre of tax wheel [mm]. auto = right side of second row")
        self.argparser.add_argument(
            "--tax_y", action="store", type=FloatStepper(0.5, auto=True),
            default=self.tax_y,
            help="Y centre of tax wheel [mm]. auto = second row")
        self.argparser.add_argument(
            "--card_x", action="store", type=FloatStepper(0.5, auto=True),
            default=self.card_x,
            help="X of card slot top-left corner on the board [mm]. auto = centred")
        self.argparser.add_argument(
            "--card_y", action="store", type=FloatStepper(0.5, auto=True),
            default=self.card_y,
            help="Y of card slot top-left corner on the board [mm]. auto = below wheel rows")

    # ------------------------------------------------------------------ #
    # Configuration helpers                                                #
    # ------------------------------------------------------------------ #

    def _wheel_cfg(self, group: str) -> _WheelCfg:
        return _WheelCfg(
            outer_diameter=getattr(self, f"{group}_outer_diameter"),
            score_min=getattr(self, f"score_{group}_min"),
            score_max=getattr(self, f"score_{group}_max"),
            score_radius=getattr(self, f"score_{group}_radius"),
            score_angle=getattr(self, f"score_{group}_angle"),
            crenel_enabled=self.crenel_enabled,
            crenel_depth=self.crenel_depth,
            crenel_width=self.crenel_width,
            crenel_shape=self.crenel_shape,
            crenel_rounded=self.crenel_rounded,
            crenel_radius=self.crenel_radius,
            font_size=getattr(self, f"font_{group}_size"),
            font_font=getattr(self, f"font_{group}_font"),
            font_bold=getattr(self, f"font_{group}_bold"),
            font_italic=getattr(self, f"font_{group}_italic"),
            font_font_as_path=getattr(self, f"font_{group}_font_as_path"),
        )

    # ------------------------------------------------------------------ #
    # Score numbers                                                        #
    # ------------------------------------------------------------------ #

    def _draw_score_numbers(self, cx: float, cy: float, label_r: float,
                            ctx: Context, cfg: _WheelCfg) -> None:
        n = cfg.score_max - cfg.score_min + 1
        if n < 1:
            return
        angle_step_rad = 2.0 * math.pi / n
        ctx.set_font(cfg.font_font, bold=cfg.font_bold, italic=cfg.font_italic,
                     as_path=cfg.font_font_as_path)
        self.set_source_color(Color.ETCHING)
        for i, score in enumerate(range(cfg.score_min, cfg.score_max + 1)):
            theta = math.pi + i * angle_step_rad
            tx = cx + label_r * math.cos(theta)
            ty = cy + label_r * math.sin(theta)
            text_angle = math.degrees(theta) + 90.0 + cfg.score_angle
            with self.saved_context():
                self.text(str(score), x=tx, y=ty, angle=text_angle,
                          align="middle center",
                          fontsize=cfg.font_size, color=Color.ETCHING)
        ctx.stroke()

    # ------------------------------------------------------------------ #
    # Outer crenels                                                        #
    # ------------------------------------------------------------------ #

    def _draw_outer_crenels(self, cx: float, cy: float, ro: float,
                            ctx: Context, cfg: _WheelCfg) -> None:
        self.parts.draw_outer_crenels(
            cx, cy, ro, ctx,
            n=cfg.score_max - cfg.score_min + 1,
            depth=cfg.crenel_depth,
            shape=cfg.crenel_shape,
            width=cfg.crenel_width,
            rounded=cfg.crenel_rounded,
            radius=cfg.crenel_radius,
        )

    # ------------------------------------------------------------------ #
    # Single ring                                                          #
    # ------------------------------------------------------------------ #

    def _draw_ring(self, cx: float, cy: float, ctx: Context, cfg: _WheelCfg) -> None:
        ro = cfg.outer_diameter / 2
        if cfg.crenel_enabled:
            self._draw_outer_crenels(cx, cy, ro, ctx, cfg)
        else:
            self.set_source_color(Color.OUTER_CUT)
            self.circle(cx, cy, ro)
        if self.magnet_diameter > 0.0:
            self.hole(cx, cy, d=self.magnet_diameter)
        label_r = (cfg.score_radius if cfg.score_radius is not None
                   else ro - cfg.font_size * 0.4)
        self._draw_score_numbers(cx, cy, label_r, ctx, cfg)

    # ------------------------------------------------------------------ #
    # Board geometry                                                       #
    # ------------------------------------------------------------------ #

    def _board_geometry(self) -> dict:
        r_commander = self.commander_outer_diameter / 2
        r_life = self.life_outer_diameter / 2
        r_tax = self.tax_outer_diameter / 2
        m = self.board_margin
        ws = self.wheel_spacing
        rs = self.row_spacing

        # ---- Row / slot dimensions (orientation-aware) ---- #
        if self.commander_vertical:
            commander_row_w = self.commander_outer_diameter
            commander_row_h = 3 * self.commander_outer_diameter + 2 * ws
        else:
            commander_row_w = 3 * self.commander_outer_diameter + 2 * ws
            commander_row_h = self.commander_outer_diameter

        if self.life_vertical:
            life_row_w = self.life_outer_diameter
            life_row_h = 2 * self.life_outer_diameter + ws
        else:
            life_row_w = 2 * self.life_outer_diameter + ws
            life_row_h = self.life_outer_diameter

        # combined row 2: life group + gap + tax wheel (used only for auto-layout)
        row2_w = life_row_w + ws + self.tax_outer_diameter
        row2_h = max(life_row_h, self.tax_outer_diameter)
        slot_w = self.card_width + 2 * self.card_slot_margin
        slot_h = self.card_height + 2 * self.card_slot_margin

        # ---- Auto-layout: compute group centres from stacked rows ---- #
        content_w = max(commander_row_w, row2_w, slot_w)
        auto_cx = m + content_w / 2

        auto_commander_y = m + commander_row_h / 2

        y_row2_top = m + commander_row_h + rs
        # Each element is top-aligned within row 2
        auto_life_y = y_row2_top + life_row_h / 2
        auto_tax_y  = y_row2_top + self.tax_outer_diameter / 2

        # Horizontal auto positions: life and tax placed side by side, centred as a unit
        row2_x0 = m + (content_w - row2_w) / 2
        auto_life_x = row2_x0 + life_row_w / 2
        auto_tax_x  = row2_x0 + life_row_w + ws + r_tax

        auto_card_top = y_row2_top + row2_h + rs
        auto_board_w = content_w + 2 * m
        auto_board_h = auto_card_top + slot_h + m

        # ---- Resolve board size first (needed for negative-from-edge coords) ---- #
        board_w = self.board_width  if self.board_width  is not None else auto_board_w
        board_h = self.board_height if self.board_height is not None else auto_board_h

        # ---- Resolve element positions ---- #
        # Negative value → distance from far edge (right / bottom).
        cmd_x = _resolve(self.commander_x, auto_cx,                          board_w)
        cmd_y = _resolve(self.commander_y, auto_commander_y,                  board_h)
        lx    = _resolve(self.life_x,      auto_life_x,                       board_w)
        ly    = _resolve(self.life_y,      auto_life_y,                       board_h)
        tx    = _resolve(self.tax_x,       auto_tax_x,                        board_w)
        ty    = _resolve(self.tax_y,       auto_tax_y,                        board_h)
        cx    = _resolve(self.card_x,      m + (content_w - slot_w) / 2,     board_w)
        cy    = _resolve(self.card_y,      auto_card_top,                     board_h)

        # ---- Derive individual wheel centres from group centres ---- #
        # Commander: 3 wheels centred on (cmd_x, cmd_y)
        if self.commander_vertical:
            commander_centers: list[tuple[float, float]] = [
                (cmd_x,
                 cmd_y - commander_row_h / 2 + r_commander + i * (self.commander_outer_diameter + ws))
                for i in range(3)
            ]
        else:
            commander_centers = [
                (cmd_x - commander_row_w / 2 + r_commander + i * (self.commander_outer_diameter + ws),
                 cmd_y)
                for i in range(3)
            ]

        # Life: 2 wheels centred on (lx, ly)
        if self.life_vertical:
            life_centers: list[tuple[float, float]] = [
                (lx,
                 ly - life_row_h / 2 + r_life + i * (self.life_outer_diameter + ws))
                for i in range(2)
            ]
        else:
            life_centers = [
                (lx - life_row_w / 2 + r_life + i * (self.life_outer_diameter + ws), ly)
                for i in range(2)
            ]

        # Tax: single wheel centre at (tx, ty)
        tax_center: tuple[float, float] = (tx, ty)

        return {
            "board_w": board_w,
            "board_h": board_h,
            "commander_centers": commander_centers,
            "life_centers": life_centers,
            "tax_center": tax_center,
            "slot_x": cx,
            "slot_y": cy,
            "slot_w": slot_w,
            "slot_h": slot_h,
        }

    # ------------------------------------------------------------------ #
    # Board piece                                                          #
    # ------------------------------------------------------------------ #

    def _draw_board(self, move: str = "") -> None:
        geom = self._board_geometry()
        board_w = geom["board_w"]
        board_h = geom["board_h"]

        if self.move(board_w, board_h, move, before=True):
            return

        ctx = cast(Context, self.ctx)

        # Outer board outline
        self.set_source_color(Color.OUTER_CUT)
        ctx.rectangle(0, 0, board_w, board_h)

        # Magnet pockets for each wheel
        if self.magnet_diameter > 0.0:
            for wx, wy in geom["commander_centers"]:
                self.hole(wx, wy, d=self.magnet_diameter)
            for wx, wy in geom["life_centers"]:
                self.hole(wx, wy, d=self.magnet_diameter)
            self.hole(*geom["tax_center"], d=self.magnet_diameter)

        # Card slot cutout
        self.set_source_color(Color.INNER_CUT)
        ctx.rectangle(geom["slot_x"], geom["slot_y"], geom["slot_w"], geom["slot_h"])

        self.move(board_w, board_h, move)

    # ------------------------------------------------------------------ #
    # Ring pieces                                                          #
    # ------------------------------------------------------------------ #

    def _draw_commander_rings(self, ctx: Context, move: str = "") -> None:
        cfg = self._wheel_cfg("commander")
        r = cfg.outer_diameter / 2
        ws = self.wheel_spacing
        if self.commander_vertical:
            row_w, row_h = cfg.outer_diameter, 3 * cfg.outer_diameter + 2 * ws
        else:
            row_w, row_h = 3 * cfg.outer_diameter + 2 * ws, cfg.outer_diameter

        if self.move(row_w, row_h, move, before=True):
            return

        for i in range(3):
            if self.commander_vertical:
                self._draw_ring(r, r + i * (cfg.outer_diameter + ws), ctx, cfg)
            else:
                self._draw_ring(r + i * (cfg.outer_diameter + ws), r, ctx, cfg)

        self.move(row_w, row_h, move)

    def _draw_life_rings(self, ctx: Context, move: str = "") -> None:
        cfg = self._wheel_cfg("life")
        r = cfg.outer_diameter / 2
        ws = self.wheel_spacing
        if self.life_vertical:
            row_w, row_h = cfg.outer_diameter, 2 * cfg.outer_diameter + ws
        else:
            row_w, row_h = 2 * cfg.outer_diameter + ws, cfg.outer_diameter

        if self.move(row_w, row_h, move, before=True):
            return

        for i in range(2):
            if self.life_vertical:
                self._draw_ring(r, r + i * (cfg.outer_diameter + ws), ctx, cfg)
            else:
                self._draw_ring(r + i * (cfg.outer_diameter + ws), r, ctx, cfg)

        self.move(row_w, row_h, move)

    def _draw_tax_ring(self, ctx: Context, move: str = "") -> None:
        cfg = self._wheel_cfg("tax")
        r = cfg.outer_diameter / 2

        if self.move(cfg.outer_diameter, cfg.outer_diameter, move, before=True):
            return

        self._draw_ring(r, r, ctx, cfg)

        self.move(cfg.outer_diameter, cfg.outer_diameter, move)

    # ------------------------------------------------------------------ #
    # Render                                                               #
    # ------------------------------------------------------------------ #

    def render(self) -> None:
        ctx = cast(Context, self.ctx)

        self._draw_board(move="right")
        self._draw_commander_rings(ctx, move="right")
        self._draw_life_rings(ctx, move="up")
        self._draw_tax_ring(ctx, move="up")
