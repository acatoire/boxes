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

from boxes import *


class BoxWithDrawer(Boxes):
    """Two-piece outer box with a separate-height sliding drawer."""

    ui_group = "Box"

    description = """
A two-piece box where the inner volume can be filled with a dedicated drawer.
Use *drawer_h* to control drawer height independently from *h* / *hi*.
"""

    x: float = 100.0
    y: float = 100.0
    h: float = 100.0
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
        h = self.h
        hi = self.hi or self.h
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
        shelf_h = drawer_h if self.drawer_opening else 0
        drawer_x = max(t, x - (2 * t + 2 * p))
        drawer_y = max(t, y - (2 * t + 2 * p))

        def shelf_holes_cb(length: float) -> None:
            self.set_source_color(Color.INNER_CUT)
            self.fingerHolesAt(0, shelf_h + t / 2, length, angle=0)

        inner_front_h = max(t, hi - drawer_h - p)

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
                                         label=f"{shell_name} back",
                                         callback=[lambda xd=x + d: shelf_holes_cb(xd)],
                                         move="right")
                else:
                    self.rectangularWall(x + d, height, "fFeF", label=f"{shell_name} front", move="right")

                if i == 0 and self.drawer_opening:
                    self.rectangularWall(y + d, height, "ffef",
                                         label=f"{shell_name} right",
                                         callback=[lambda yd=y + d: shelf_holes_cb(yd)],
                                         move="right")
                else:
                    self.rectangularWall(y + d, height, "ffef", label=f"{shell_name} right", move="right")

                if i == 0 and self.drawer_opening:
                    self.rectangularWall(x + d, height, "fFeF",
                                         label=f"{shell_name} back",
                                         callback=[lambda xd=x + d: shelf_holes_cb(xd)],
                                         move="right")
                else:
                    self.rectangularWall(x + d, height, "fFeF", label=f"{shell_name} back", move="right")

                if i == 0 and self.drawer_opening:
                    self.rectangularWall(y + d, height, "ffef",
                                         label=f"{shell_name} left",
                                         callback=[lambda yd=y + d: shelf_holes_cb(yd)],
                                         move="right")
                else:
                    self.rectangularWall(y + d, height, "ffef", label=f"{shell_name} left", move="right")
            self.rectangularWall(y, height, "ffef", move="up only")

        self.rectangularWall(x, y, "hhhh", label="inner bottom", bedBolts=None, move="right")
        self.rectangularWall(x + d, y + d, "FFFF", label="outer top", bedBolts=None, move="right")
        if self.drawer_opening:
            self.rectangularWall(x, y, "ffff", label="inner shelf bottom", bedBolts=None, move="right")

        self.rectangularWall(drawer_x, drawer_h, "FFeF", label="drawer front", move="right")
        self.rectangularWall(drawer_y, drawer_h, "ffef", label="drawer right", move="right")
        self.rectangularWall(drawer_x, drawer_h, "FFeF", label="drawer back", move="right")
        self.rectangularWall(drawer_y, drawer_h, "ffef", label="drawer left", move="right")
        self.rectangularWall(drawer_x, drawer_y, "FfFf", label="drawer bottom", move="right")
