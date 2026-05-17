# Copyright (C) 2026 Florian Festi
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

from typing import cast

from boxes import *
from boxes.drawing import Context


class _FlushEdge(edges.BaseEdge):
    """Plain straight edge with the same bounding-box spacing as FingerHoleEdge ('h').
    Use it as a drop-in replacement for 'h' when you want the same layout footprint
    but no finger holes drawn (e.g. a flush/closed side of a panel)."""

    def __call__(self, length: float, **kw) -> None:
        self.boxes.edge(length)

    def startWidth(self) -> float:
        # mirrors FingerHoleEdge.startWidth()
        return self.settings.edge_width + self.settings.thickness

    def margin(self) -> float:
        return 0.0


class BoxWithDrawer(Boxes):
    """Two-piece outer box with a separate-height sliding drawer."""

    ui_group = "Box"

    description = """
A two-piece box where the inner volume can be filled with a dedicated drawer.
Use *drawer_h* to control drawer height independently from *h* / *hi*.
"""

    x: float = 100.0
    y: float = 100.0
    box_h: float = 100.0
    hi: float = 0.0
    outside: bool = False
    play: float = 0.15
    drawer_h: float = 25.0
    drawer_opening: bool = False

    def __init__(self) -> None:
        Boxes.__init__(self)
        self.buildArgParser("x", "y", "h", "hi", "outside")
        self.addSettingsArgs(edges.FingerJointSettings, finger=2.0, space=2.0)
        self.argparser.add_argument(
            "--play",
            action="store",
            type=float,
            default=0.15,
            help="play between fitting parts as multiple of the wall thickness",
        )
        self.argparser.add_argument(
            "--drawer_h",
            action="store",
            type=float,
            default=25.0,
            help="height of the inner drawer [mm]",
        )
        self.argparser.add_argument(
            "--drawer_opening",
            action="store",
            type=boolarg,
            default=False,
            help="reduce inner front wall to let drawer slide under it",
        )

    def render(self) -> None:
        x = self.x
        y = self.y
        h = self.box_h
        hi = self.hi or self.box_h
        drawer_h = self.drawer_h
        t = self.thickness
        p = self.play * t

        if self.outside:
            x -= 4 * t + 2 * p
            y -= 4 * t + 2 * p
            h -= 2 * t
            hi -= 2 * t
            drawer_h -= 2 * t

        drawer_h = max(t, min(drawer_h, hi))
        drawer_x = max(t, x - (2 * t + 2 * p))
        # In drawer_opening mode the drawer slides in from the front (under the split wall),
        # so its depth equals the full inner depth y – no front-wall reduction needed.
        drawer_y = y if self.drawer_opening else max(t, y - (2 * t + 2 * p))

        def wall_cb(length: float, line_color: list[float]) -> None:
            """Finger holes for shelf + split line at drawer_h in the given color."""
            with self.saved_context():
                self.set_source_color(Color.INNER_CUT)
                self.fingerHolesAt(0, drawer_h + t / 2, length, angle=0)
            with self.saved_context():
                self.set_source_color(line_color)
                self.moveTo(0, drawer_h)
                self.edge(length)
                ctx = cast(Context, self.ctx)
                ctx.stroke()  # commit path NOW with line_color, before restore()

        # Make the second shell slightly bigger so it slips over the first one.
        self.edges["f"].settings.setValues(
            t,
            False,
            edge_width=self.edges["f"].settings.edge_width + p,
        )

        shell_names = ("inner", "outer")
        for i, shell_name in enumerate(shell_names):
            d = i * 2 * (t + p)
            height = hi if i == 0 else h
            with self.saved_context():
                if i == 0 and self.drawer_opening:
                    self.rectangularWall(x + d, height, "fFeF",
                                         label=f"{shell_name} front",
                                         callback=[lambda xd=x + d: wall_cb(xd, Color.OUTER_CUT)],
                                         move="right")
                else:
                    self.rectangularWall(x + d, height, "fFeF", label=f"{shell_name} front", move="right")

                if i == 0 and self.drawer_opening:
                    self.rectangularWall(y + d, height, "ffef",
                                         label=f"{shell_name} right",
                                         callback=[lambda yd=y + d: wall_cb(yd, Color.ETCHING)],
                                         move="right")
                else:
                    self.rectangularWall(y + d, height, "ffef", label=f"{shell_name} right", move="right")

                if i == 0 and self.drawer_opening:
                    self.rectangularWall(x + d, height, "fFeF",
                                         label=f"{shell_name} back",
                                         callback=[lambda xd=x + d: wall_cb(xd, Color.OUTER_CUT)],
                                         move="right")
                else:
                    self.rectangularWall(x + d, height, "fFeF", label=f"{shell_name} back", move="right")

                if i == 0 and self.drawer_opening:
                    self.rectangularWall(y + d, height, "ffef",
                                         label=f"{shell_name} left",
                                         callback=[lambda yd=y + d: wall_cb(yd, Color.ETCHING)],
                                         move="right")
                else:
                    self.rectangularWall(y + d, height, "ffef", label=f"{shell_name} left", move="right")
            self.rectangularWall(y, height, "ffef", move="up only")

        with self.saved_context():
            if self.drawer_opening:
                self.rectangularWall(x, y, "ffff", label="shelf bottom", bedBolts=None, move="right")
            self.rectangularWall(x + d, y + d, "FFFF", label="outer top", bedBolts=None, move="right")

            if self.drawer_opening:
              # _FlushEdge: same spacing as 'h' but no holes → exact same layout size
              fe = _FlushEdge(self, self.edges["h"].settings)
              self.rectangularWall(x, y, [fe, self.edges["h"], fe, self.edges["h"]], label="inner bottom flush", bedBolts=None, move="right")
            else:
              self.rectangularWall(x, y, "hhhh", label="inner bottom", bedBolts=None, move="right")

        # layout spacer: advances past the plates row (uses "hhhh" – tallest edge spacing in the row)
        self.rectangularWall(x + d, y + d, "hhhh", move="up only")

        with self.saved_context():
            self.rectangularWall(drawer_x, drawer_h, "FFeF", label="drawer front", move="right")
            self.rectangularWall(drawer_y, drawer_h, "ffef", label="drawer right", move="right")
            self.rectangularWall(drawer_x, drawer_h, "FFeF", label="drawer back", move="right")
            self.rectangularWall(drawer_y, drawer_h, "ffef", label="drawer left", move="right")
            self.rectangularWall(drawer_x, drawer_y, "FfFf", label="drawer bottom", move="right")
        # layout spacer: advances past the drawer row
        self.rectangularWall(drawer_x, drawer_y, "FfFf", move="up only")
