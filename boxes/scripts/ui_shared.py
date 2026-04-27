# Copyright (C) 2026 Boxes.py contributors
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

from collections.abc import Callable

# Maps each interface identifier to its (URL, emoji+label) pair.
_INTERFACES: list[tuple[str, str, str]] = [
    ("Gallery", "\U0001f5bc\ufe0f", "Gallery"),
    ("Menu",    "\U0001f4cb",       "Menu"),
    ("TouchHub","\U0001f4f1",       "Touch"),
]

_ONCHANGE = (
    "var v=this.value;"
    "try{localStorage.setItem('boxes-ui-mode',v==='TouchHub'?'touch':'legacy')}catch(e){};"
    "window.location.href=v"
)


def gen_interface_select_html(current: str, _: Callable[[str], str]) -> str:
    """Return the ``<div class="dropdown-interface">`` HTML snippet.

    *current* is one of ``"Gallery"``, ``"Menu"``, ``"TouchHub"`` or ``""``
    (no pre-selection, show a disabled placeholder instead).
    *_* is the gettext translation callable.
    """
    if current:
        opts = "".join(
            f'<option value="{url}"{" selected" if url == current else ""}>'
            f"{emoji} {_(label)}</option>"
            for url, emoji, label in _INTERFACES
        )
    else:
        placeholder = f'<option value="" disabled selected>{_("Choose\u2026")}</option>'
        opts = placeholder + "".join(
            f'<option value="{url}">{emoji} {_(label)}</option>'
            for url, emoji, label in _INTERFACES
        )

    return (
        f'<div class="dropdown-interface">\U0001f5a5\ufe0f {_("Interface:")}'
        f'<select onchange="{_ONCHANGE}">{opts}</select>'
        f"</div>"
    )
