# Copyright (C) 2016-2017 Florian Festi
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
from __future__ import annotations
pass
class ColorsUIMixin:
    """Mixin that renders the /settings (Colors) page in touch style."""
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
    def serveColors(self, environ: object, start_response: object, lang: object) -> list[bytes]:
        """Render the /settings page (touch style)."""
        _ = lang.gettext  # type: ignore[attr-defined]
        lang_name = lang.info().get("language", None)  # type: ignore[attr-defined]
        langparam = f"?language={lang_name}" if lang_name else ""
        from boxes.Color import Color
        named_colors: list[tuple[str, str]] = [
            (cname, Color.to_hex(getattr(Color, cname)))
            for cname in ("BLACK", "BLUE", "GREEN", "RED", "CYAN", "YELLOW", "MAGENTA", "WHITE")
        ]
        rows: list[str] = []
        for role, (label, desc) in Color.ROLE_LABELS.items():
            default_hex = Color.to_hex(getattr(Color, role))
            options = "\n".join(
                f'        <option value="{hex_val}"{" selected" if hex_val == default_hex else ""}>'
                f"{cname} ({hex_val})</option>"
                for cname, hex_val in named_colors
            )
            rows.append(
                f'  <div class="cs-row">\n'
                f'    <div class="cs-label"><label for="color_{role}">{label}</label></div>\n'
                f'    <select class="cs-select" id="color_{role}" data-role="{role}" onchange="onColorChange(this)">\n'
                f'{options}\n'
                f'    </select>\n'
                f'    <span class="cs-desc">{desc}</span>\n'
                f'  </div>'
            )
        rows_html = "\n".join(rows)
        touch_css = self.genHTMLTouchCSS()
        touch_js = self.genHTMLTouchJS()
        touch_header = self._touch_header_html(lang, back_url=f"TouchHub{langparam}", back_icon_only=True)
        page = (
            self.genHTMLStart(lang) + "\n"
            "<head>\n"
            f"  <title>{_('Colors')} \u2013 {_('Boxes.py')}</title>\n"
            f"  {self.genHTMLMeta()}\n"
            f"  {self.genHTMLCSS()}\n"
            f"  {touch_css}\n"
            f"  {self.genHTMLJS()}\n"
            f"  {touch_js}\n"
            "  <style>\n"
            "    body.touch-colors{margin:0;padding:0;min-height:100dvh;display:flex;flex-direction:column;background:var(--th-page-bg);font-size:17px;}\n"
            "    .cs-body{flex:1;padding:20px 24px;overflow-y:auto;}\n"
            "    .cs-body h2{margin:0 0 6px;color:#333;}\n"
            "    .cs-body>p{margin:0 0 20px;color:#666;font-size:.9em;}\n"
            "    .cs-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:12px;margin-bottom:24px;}\n"
            "    .cs-row{background:#fff;border-radius:10px;box-shadow:0 2px 6px rgba(0,0,0,.09);padding:14px 16px;display:flex;flex-direction:column;gap:8px;}\n"
            "    .cs-label{display:flex;align-items:center;gap:10px;font-weight:bold;font-size:.95em;color:#222;}\n"
            "    .touch-colors .color-swatch{display:inline-block;width:28px;height:28px;border-radius:6px;border:2px solid rgba(0,0,0,.15);flex-shrink:0;vertical-align:middle;margin-left:8px;transition:background .2s;}\n"
            "    .cs-select{height:44px;font-size:.95em;padding:0 10px;border-radius:8px;border:1px solid #ccc;background:#fafafa;cursor:pointer;width:100%;box-sizing:border-box;}\n"
            "    .cs-desc{font-size:.82em;color:#666;line-height:1.35;}\n"
            "    .cs-actions{display:flex;gap:12px;flex-wrap:wrap;align-items:center;}\n"
            "    .cs-btn{background:var(--th-accent);color:#fff;border:none;border-radius:10px;padding:0 24px;min-height:48px;font-size:1em;font-family:inherit;font-weight:bold;cursor:pointer;transition:background .15s;}\n"
            "    .cs-btn:hover{background:var(--th-accent2);}\n"
            "    .cs-btn.secondary{background:#666;}\n"
            "    .cs-btn.secondary:hover{background:#444;}\n"
            "    #color-settings-status{color:green;font-weight:bold;}\n"
            "    #import-file{display:none;}\n"
            "  </style>\n"
            "</head>\n"
            f'<body class="touch-colors" onload="initColorSettingsPage()">\n'
            f"\n{touch_header}\n\n"
            '<div class="cs-body">\n'
            f"  <h2>{_('Colors')}</h2>\n"
            f"  <p>{_('Choose the SVG stroke color for each laser operation. Changes are saved instantly in your browser.')}</p>\n"
            '  <div class="cs-grid">\n'
            f"{rows_html}\n"
            "  </div>\n"
            '  <div class="cs-actions">\n'
            f'    <button class="cs-btn" onclick="saveColorSettingsExplicit()">{_("Save")}</button>\n'
            f'    <button class="cs-btn secondary" onclick="exportColorSettings()">{_("Export JSON")}</button>\n'
            f'    <button class="cs-btn secondary" onclick="document.getElementById(\'import-file\').click()">{_("Import JSON")}</button>\n'
            f'    <input type="file" id="import-file" accept=".json,application/json" onchange="importColorSettings(this)">\n'
            f'    <button class="cs-btn secondary" onclick="resetColorSettings()">{_("Reset to defaults")}</button>\n'
            f'    <span id="color-settings-status" style="display:none">{_("Saved.")}</span>\n'
            "  </div>\n"
            "</div>\n\n</body>\n</html>\n"
        )
        start_response("200 OK", [("Content-type", "text/html; charset=utf-8")])  # type: ignore[operator]
        return [page.encode("utf-8")]
