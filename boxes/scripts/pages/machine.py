# Copyright (C) 2016-2017 Florian Festi
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


class MachineUIMixin:
    """Mixin that renders the /machine (laser engraving zone) settings page."""

    static_url: str

    def genHTMLStart(self, lang: object) -> str:
        raise NotImplementedError

    def genHTMLMeta(self) -> str:
        raise NotImplementedError

    def genHTMLCSS(self) -> str:
        raise NotImplementedError

    def genHTMLJS(self) -> str:
        raise NotImplementedError

    def genHTMLTouchCSS(self) -> str:
        raise NotImplementedError

    def genHTMLTouchJS(self) -> str:
        raise NotImplementedError

    def _touch_header_html(self, lang: object, back_url: str = "", back_icon_only: bool = False) -> str:
        raise NotImplementedError

    def serveMachine(self, environ: object, start_response: object, lang: object) -> list[bytes]:
        """Render the /machine settings page (touch style)."""
        _ = lang.gettext  # type: ignore[attr-defined]
        lang_name = lang.info().get("language", None)  # type: ignore[attr-defined]
        langparam = f"?language={lang_name}" if lang_name else ""

        touch_header = self._touch_header_html(lang, back_url=f"TouchHub{langparam}", back_icon_only=True)

        # Known machines: (brand, model, width_mm, height_mm)
        known_machines: list[tuple[str, str, int, int]] = [
            ("Ortur", "Master 3",  400, 380),
            ("Ortur", "H20 40W",   410, 275),
            ("xTool", "M1 Ultra",  300, 300),
        ]

        # Group by brand (already sorted)
        brands: dict[str, list[tuple[str, int, int]]] = {}
        for brand, model, w, h in known_machines:
            brands.setdefault(brand, []).append((model, w, h))

        preset_rows: list[str] = []
        for brand in sorted(brands):
            preset_rows.append(
                f'    <tr class="ms-brand-row"><td colspan="3">'
                f'<strong>{brand}</strong></td></tr>\n'
            )
            for model, w, h in brands[brand]:
                preset_rows.append(
                    f'    <tr class="ms-preset-row">'
                    f'<td>{model}</td>'
                    f'<td>{w} \u00d7 {h} mm</td>'
                    f'<td><button class="ms-btn ms-btn-use" '
                    f'onclick="machineUsePreset({w},{h})">{_("Use")}</button></td>'
                    f'</tr>\n'
                )

        presets_html = "".join(preset_rows)

        page = (
            self.genHTMLStart(lang) + "\n"
            "<head>\n"
            f"  <title>{_('Machine')} \u2013 {_('Boxes.py')}</title>\n"
            f"  {self.genHTMLMeta()}\n"
            f"  {self.genHTMLCSS()}\n"
            f"  {self.genHTMLTouchCSS()}\n"
            f"  {self.genHTMLJS()}\n"
            f"  {self.genHTMLTouchJS()}\n"
            "  <style>\n"
            "    body.touch-machine{margin:0;padding:0;min-height:100dvh;display:flex;flex-direction:column;background:var(--th-page-bg);font-size:17px;}\n"
            "    .ms-body{flex:1;padding:20px 24px;overflow-y:auto;max-width:700px;}\n"
            "    .ms-body h2{margin:0 0 6px;color:#333;}\n"
            "    .ms-body>p{margin:0 0 20px;color:#666;font-size:.9em;}\n"
            "    .ms-section{background:#fff;border-radius:10px;box-shadow:0 2px 6px rgba(0,0,0,.09);padding:18px 20px;margin-bottom:20px;}\n"
            "    .ms-section h3{margin:0 0 14px;font-size:1em;color:#333;}\n"
            "    .ms-dims{display:flex;gap:16px;align-items:center;flex-wrap:wrap;margin-bottom:10px;}\n"
            "    .ms-dims label{font-size:.95em;color:#444;display:flex;align-items:center;gap:8px;}\n"
            "    .ms-dims input{height:44px;width:90px;font-size:1em;text-align:center;border:1px solid #bbb;border-radius:8px;padding:0 8px;box-sizing:border-box;}\n"
            "    .ms-table{width:100%;border-collapse:collapse;font-size:.93em;}\n"
            "    .ms-table td{padding:8px 10px;border-bottom:1px solid #f0ebe0;vertical-align:middle;}\n"
            "    .ms-brand-row td{background:#f5f0e8;font-weight:bold;color:#555;padding:6px 10px;}\n"
            "    .ms-btn{border:none;border-radius:8px;padding:0 16px;height:36px;font-size:.9em;font-family:inherit;cursor:pointer;transition:background .15s;}\n"
            "    .ms-btn-use{background:var(--th-accent);color:#fff;font-weight:bold;}\n"
            "    .ms-btn-use:hover{background:var(--th-accent2);}\n"
            "    .ms-actions{display:flex;gap:12px;flex-wrap:wrap;align-items:center;margin-top:8px;}\n"
            "    .ms-save-btn{background:var(--th-accent);color:#fff;border:none;border-radius:10px;padding:0 28px;min-height:48px;font-size:1em;font-family:inherit;font-weight:bold;cursor:pointer;transition:background .15s;}\n"
            "    .ms-save-btn:hover{background:var(--th-accent2);}\n"
            "    #ms-status{color:#2e7d32;font-weight:bold;}\n"
            "  </style>\n"
            "</head>\n"
            f'<body class="touch-machine" onload="initMachineSettingsPage()">\n'
            f"\n{touch_header}\n\n"
            '<div class="ms-body">\n'
            f"  <h2>\u2699 {_('Machine')}</h2>\n"
            f"  <p>{_('Set your laser engraving zone size. Used on the generator page to check if the design fits.')}</p>\n"
            '  <div class="ms-section">\n'
            f"    <h3>{_('Custom size')}</h3>\n"
            '    <div class="ms-dims">\n'
            f'      <label>{_("Width (mm)")}<input type="number" id="machine-w" min="1" max="9999" step="1" value="300"></label>\n'
            f'      <label>{_("Height (mm)")}<input type="number" id="machine-h" min="1" max="9999" step="1" value="300"></label>\n'
            "    </div>\n"
            '    <div class="ms-actions">\n'
            f'      <button class="ms-save-btn" onclick="saveMachineSettingsPage()">{_("Save")}</button>\n'
            f'      <span id="ms-status" style="display:none">{_("Saved.")}</span>\n'
            "    </div>\n"
            "  </div>\n"
            '  <div class="ms-section">\n'
            f"    <h3>{_('Machine presets')}</h3>\n"
            '    <table class="ms-table">\n'
            f"{presets_html}"
            "    </table>\n"
            "  </div>\n"
            "</div>\n\n"
            "<script>\n"
            "function initMachineSettingsPage() {\n"
            "    const cfg = loadMachineConfig();\n"
            "    document.getElementById('machine-w').value = cfg.w;\n"
            "    document.getElementById('machine-h').value = cfg.h;\n"
            "}\n"
            "function saveMachineSettingsPage() {\n"
            "    const w = parseFloat(document.getElementById('machine-w').value) || 300;\n"
            "    const h = parseFloat(document.getElementById('machine-h').value) || 300;\n"
            "    saveMachineConfig(w, h);\n"
            "    const st = document.getElementById('ms-status');\n"
            "    if (st) { st.style.display='inline'; clearTimeout(st._t); st._t=setTimeout(()=>{st.style.display='none';},1500); }\n"
            "}\n"
            "function machineUsePreset(w, h) {\n"
            "    document.getElementById('machine-w').value = w;\n"
            "    document.getElementById('machine-h').value = h;\n"
            "    saveMachineSettingsPage();\n"
            "}\n"
            "</script>\n"
            "</body>\n</html>\n"
        )
        start_response("200 OK", [("Content-type", "text/html; charset=utf-8")])  # type: ignore[operator]
        return [page.encode("utf-8")]
