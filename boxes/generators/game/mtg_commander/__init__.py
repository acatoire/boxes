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


class MtgCommanderZone(Boxes):
    """MTG Commander Zone – board with 6 score wheels and a commander card slot"""

    ui_group = "Game"
    tags = ["unstable", "tcg"]

    description = """
A laser-cut MTG Commander Zone tracker with **six independent score wheels** and
a **commander card slot**.

**Wheel groups**

* **3 × large wheels** (default 0–20) – track life totals or commander damage.
* **2 × medium wheels** (default 0–10) – track per-opponent commander damage.
* **1 × small wheel** (default 0–5) – track poison / experience counters.

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
    large_outer_diameter: float = 45.0
    medium_outer_diameter: float = 35.0
    small_outer_diameter: float = 25.0

    board_margin: float = 6.0
    wheel_spacing: float = 4.0
    row_spacing: float = 5.0
    magnet_diameter: float = 5.0

    card_width: float = 63.0
    card_height: float = 88.0
    card_slot_margin: float = 2.0

    # font (shared across all wheels)
    font_size: float = 6.0
    font_font: str = "sans-serif"
    font_bold: bool = False
    font_italic: bool = False
    font_font_as_path: bool = True

    # score – large wheels
    score_large_min: int = 0
    score_large_max: int = 20
    score_large_radius: float | None = None
    score_large_angle: float = -90.0

    # score – medium wheels
    score_medium_min: int = 0
    score_medium_max: int = 10
    score_medium_radius: float | None = None
    score_medium_angle: float = -90.0

    # score – small wheel
    score_small_min: int = 0
    score_small_max: int = 5
    score_small_radius: float | None = None
    score_small_angle: float = -90.0

    # crenel (shared across all wheels)
    crenel_enabled: bool = True
    crenel_depth: float = 3.0
    crenel_width: float = 0.3
    crenel_shape: str = "radial"
    crenel_rounded: bool = True
    crenel_radius: float = 0.0

    def __init__(self) -> None:
        Boxes.__init__(self)

        self.addSettingsArgs(FontSettings, prefix="font",
                             size=self.font_size, font=self.font_font,
                             bold=self.font_bold, italic=self.font_italic)
        self.addSettingsArgs(ScoreSettings, prefix="score_large",
                             title="Score Large Wheels Settings",
                             min=self.score_large_min, max=self.score_large_max,
                             radius=self.score_large_radius, angle=self.score_large_angle)
        self.addSettingsArgs(ScoreSettings, prefix="score_medium",
                             title="Score Medium Wheels Settings",
                             min=self.score_medium_min, max=self.score_medium_max,
                             radius=self.score_medium_radius, angle=self.score_medium_angle)
        self.addSettingsArgs(ScoreSettings, prefix="score_small",
                             title="Score Small Wheel Settings",
                             min=self.score_small_min, max=self.score_small_max,
                             radius=self.score_small_radius, angle=self.score_small_angle)
        self.addSettingsArgs(CrenelSettings, prefix="crenel",
                             enabled=self.crenel_enabled, depth=self.crenel_depth,
                             width=self.crenel_width, shape=self.crenel_shape,
                             rounded=self.crenel_rounded, radius=self.crenel_radius)

        self.argparser.add_argument(
            "--large_outer_diameter", action="store", type=FloatStepper(1.0),
            default=self.large_outer_diameter,
            help="Outer diameter of the large wheels [mm]")
        self.argparser.add_argument(
            "--medium_outer_diameter", action="store", type=FloatStepper(1.0),
            default=self.medium_outer_diameter,
            help="Outer diameter of the medium wheels [mm]")
        self.argparser.add_argument(
            "--small_outer_diameter", action="store", type=FloatStepper(1.0),
            default=self.small_outer_diameter,
            help="Outer diameter of the small wheel [mm]")
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
        ctx.set_font(self.font_font, bold=self.font_bold, italic=self.font_italic,
                     as_path=self.font_font_as_path)
        self.set_source_color(Color.ETCHING)
        for i, score in enumerate(range(cfg.score_min, cfg.score_max + 1)):
            theta = math.pi + i * angle_step_rad
            tx = cx + label_r * math.cos(theta)
            ty = cy + label_r * math.sin(theta)
            text_angle = math.degrees(theta) + 90.0 + cfg.score_angle
            with self.saved_context():
                self.text(str(score), x=tx, y=ty, angle=text_angle,
                          align="middle center",
                          fontsize=self.font_size, color=Color.ETCHING)
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
                   else ro - self.font_size * 0.4)
        self._draw_score_numbers(cx, cy, label_r, ctx, cfg)

    # ------------------------------------------------------------------ #
    # Board geometry                                                       #
    # ------------------------------------------------------------------ #

    def _board_geometry(self) -> dict:
        r_large = self.large_outer_diameter / 2
        r_medium = self.medium_outer_diameter / 2
        r_small = self.small_outer_diameter / 2
        m = self.board_margin
        ws = self.wheel_spacing
        rs = self.row_spacing

        # Row widths
        row1_w = 3 * self.large_outer_diameter + 2 * ws   # 3 large
        row2_w = (2 * self.medium_outer_diameter           # 2 medium
                  + self.small_outer_diameter              # 1 small
                  + 2 * ws)
        slot_w = self.card_width + 2 * self.card_slot_margin
        slot_h = self.card_height + 2 * self.card_slot_margin

        content_w = max(row1_w, row2_w, slot_w)
        board_w = content_w + 2 * m

        # Y coordinates (top-down)
        y_row1_top = m
        y_row1_bottom = m + self.large_outer_diameter
        y_row2_top = y_row1_bottom + rs
        y_row2_height = max(self.medium_outer_diameter, self.small_outer_diameter)
        y_row2_bottom = y_row2_top + y_row2_height
        y_card_top = y_row2_bottom + rs
        board_h = y_card_top + slot_h + m

        # Center-align each row horizontally within the content area
        row1_x0 = m + (content_w - row1_w) / 2
        row2_x0 = m + (content_w - row2_w) / 2
        slot_x = m + (content_w - slot_w) / 2

        # Large wheel centers (vertically centred in their row)
        y_large = y_row1_top + r_large
        large_centers: list[tuple[float, float]] = [
            (row1_x0 + r_large + i * (self.large_outer_diameter + ws), y_large)
            for i in range(3)
        ]

        # Medium wheel centers (bottom-aligned in row 2)
        cy_medium = y_row2_bottom - r_medium
        medium_centers: list[tuple[float, float]] = [
            (row2_x0 + r_medium + i * (self.medium_outer_diameter + ws), cy_medium)
            for i in range(2)
        ]

        # Small wheel center (bottom-aligned in row 2)
        cx_small = row2_x0 + 2 * self.medium_outer_diameter + 2 * ws + r_small
        cy_small = y_row2_bottom - r_small

        return {
            "board_w": board_w,
            "board_h": board_h,
            "large_centers": large_centers,
            "medium_centers": medium_centers,
            "small_center": (cx_small, cy_small),
            "slot_x": slot_x,
            "slot_y": y_card_top,
            "slot_w": slot_w,
            "slot_h": slot_h,
            "row2_w": row2_w,
            "row1_w": row1_w,
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
            for cx, cy in geom["large_centers"]:
                self.hole(cx, cy, d=self.magnet_diameter)
            for cx, cy in geom["medium_centers"]:
                self.hole(cx, cy, d=self.magnet_diameter)
            cx_s, cy_s = geom["small_center"]
            self.hole(cx_s, cy_s, d=self.magnet_diameter)

        # Card slot cutout
        self.set_source_color(Color.INNER_CUT)
        ctx.rectangle(geom["slot_x"], geom["slot_y"], geom["slot_w"], geom["slot_h"])

        self.move(board_w, board_h, move)

    # ------------------------------------------------------------------ #
    # Ring rows                                                            #
    # ------------------------------------------------------------------ #

    def _draw_large_rings(self, ctx: Context, move: str = "") -> None:
        cfg = self._wheel_cfg("large")
        r = cfg.outer_diameter / 2
        ws = self.wheel_spacing
        row_w = 3 * cfg.outer_diameter + 2 * ws
        row_h = cfg.outer_diameter

        if self.move(row_w, row_h, move, before=True):
            return

        for i in range(3):
            cx = r + i * (cfg.outer_diameter + ws)
            self._draw_ring(cx, r, ctx, cfg)

        self.move(row_w, row_h, move)

    def _draw_medium_small_rings(self, ctx: Context, move: str = "") -> None:
        cfg_m = self._wheel_cfg("medium")
        cfg_s = self._wheel_cfg("small")
        ws = self.wheel_spacing
        row_h = max(cfg_m.outer_diameter, cfg_s.outer_diameter)
        row_w = 2 * cfg_m.outer_diameter + cfg_s.outer_diameter + 2 * ws

        if self.move(row_w, row_h, move, before=True):
            return

        row_bottom = row_h
        # 2 medium wheels – bottom-aligned
        rm = cfg_m.outer_diameter / 2
        for i in range(2):
            cx = rm + i * (cfg_m.outer_diameter + ws)
            cy = row_bottom - rm
            self._draw_ring(cx, cy, ctx, cfg_m)

        # 1 small wheel – bottom-aligned
        rs_r = cfg_s.outer_diameter / 2
        cx = 2 * cfg_m.outer_diameter + 2 * ws + rs_r
        cy = row_bottom - rs_r
        self._draw_ring(cx, cy, ctx, cfg_s)

        self.move(row_w, row_h, move)

    # ------------------------------------------------------------------ #
    # Render                                                               #
    # ------------------------------------------------------------------ #

    def render(self) -> None:
        ctx = cast(Context, self.ctx)

        self._draw_board(move="up")
        self._draw_large_rings(ctx, move="up")
        self._draw_medium_small_rings(ctx, move="up")
