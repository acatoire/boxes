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

    def genHTMLMachineCSS(self) -> str:
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
            f"  {self.genHTMLMachineCSS()}\n"
            f"  {self.genHTMLJS()}\n"
            f"  {self.genHTMLTouchJS()}\n"
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
            '  <div class="ms-section">\n'
            f"    <h3>\U0001F4B6 {_('Material pricing')}</h3>\n"
            f"    <p style=\"font-size:.88em;color:#666;margin:0 0 10px\">{_('Select a material to get a cost estimate on the generator page.')}</p>\n"
            '    <table class="ms-mat-table">\n'
            '      <tr><td><input type="radio" name="ms-material" id="ms-mat-none" value=""><label for="ms-mat-none">\u2014 Aucun \u2014</label></td><td></td></tr>\n'
            '      <tr><td><input type="radio" name="ms-material" id="ms-mat-tilleul3" value="tilleul3"><label for="ms-mat-tilleul3">3mm contreplaqué Tilleul</label></td><td>25 \u20ac/m\u00b2</td></tr>\n'
            '      <tr><td><input type="radio" name="ms-material" id="ms-mat-noyer" value="noyer"><label for="ms-mat-noyer">contreplaqué Noyer</label></td><td>36 \u20ac/m\u00b2</td></tr>\n'
            "    </table>\n"
            "  </div>\n"
            '  <div class="ms-section">\n'
            f"    <h3>\U0001F4CA {_('Margin coefficient')}</h3>\n"
            f"    <p style=\"font-size:.88em;color:#666;margin:0 0 10px\">{_('Multiply the material cost by this factor (e.g. 1.5 for a 50% margin). Default: 1.')}</p>\n"
            '    <div class="ms-coef-row">\n'
            f'      <label>{_("Coefficient")}<input type="number" id="machine-margin-coef" min="0.01" max="100" step="0.01" value="1"></label>\n'
            "    </div>\n"
            "  </div>\n"
            "</div>\n\n"
            "<script>\n"
            "function initMachineSettingsPage() {\n"
            "    const cfg = loadMachineConfig();\n"
            "    document.getElementById('machine-w').value = cfg.w;\n"
            "    document.getElementById('machine-h').value = cfg.h;\n"
            "    const matVal = cfg.material || '';\n"
            "    const radios = document.querySelectorAll('input[name=\"ms-material\"]');\n"
            "    radios.forEach(r => { r.checked = (r.value === matVal); });\n"
            "    if (!Array.from(radios).some(r => r.checked)) radios[0].checked = true;\n"
            "    const coefEl = document.getElementById('machine-margin-coef');\n"
            "    if (coefEl) coefEl.value = (cfg.margin_coef !== undefined ? cfg.margin_coef : 1);\n"
            "}\n"
            "function saveMachineSettingsPage() {\n"
            "    const w = parseFloat(document.getElementById('machine-w').value) || 300;\n"
            "    const h = parseFloat(document.getElementById('machine-h').value) || 300;\n"
            "    const matRadio = document.querySelector('input[name=\"ms-material\"]:checked');\n"
            "    const mat = matRadio ? matRadio.value : '';\n"
            "    const coefEl = document.getElementById('machine-margin-coef');\n"
            "    const coef = coefEl ? (parseFloat(coefEl.value) || 1) : 1;\n"
            "    saveMachineConfig(w, h, mat, coef);\n"
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
