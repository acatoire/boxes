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
    def genHTMLColorsCSS(self) -> str:
        raise NotImplementedError
    def genHTMLTouchJS(self) -> str:
        raise NotImplementedError
    def genHTMLShopJS(self) -> str:
        raise NotImplementedError
    def genHTMLThemeInit(self) -> str:
        raise NotImplementedError
    def _touch_header_html(self, lang: object, back_url: str = "", back_icon_only: bool = False, center_html: str = "", show_dropdown: bool = True) -> str:
        raise NotImplementedError
    def _colorPreviewSVG(self) -> str:
        """Build a small inline SVG example that uses every color role.

        Each element carries a ``data-color-role`` attribute so the client-side
        JS (``updatePreviewColors``) can recolor it live when a select changes,
        without needing a server round-trip. Shapes that can be solid-filled
        carry ``data-fill-role`` too; they start as an outline only (``fill="none"``)
        and the show-fill checkbox toggles their ``fill`` attribute between
        ``none`` and the current SOLID_FILL color, so the outline stays visible
        either way.
        """
        from boxes.Color import Color
        hexes = {role: Color.to_hex(getattr(Color, role)) for role in Color.ROLE_LABELS}
        return (
            '    <svg viewBox="0 0 220 160" width="320" height="240" '
            'xmlns="http://www.w3.org/2000/svg">\n'
            f'      <rect x="10" y="10" width="200" height="140" fill="none" '
            f'stroke="{hexes["OUTER_CUT"]}" stroke-width="2" '
            f'data-color-role="OUTER_CUT"/>\n'
            f'      <circle cx="55" cy="55" r="18" fill="none" '
            f'stroke="{hexes["INNER_CUT"]}" stroke-width="2" '
            f'data-color-role="INNER_CUT"/>\n'
            f'      <rect x="150" y="37" width="36" height="36" fill="none" '
            f'stroke="{hexes["INNER_CUT"]}" stroke-width="2" '
            f'data-color-role="INNER_CUT"/>\n'
            f'      <line x1="120" y1="95" x2="190" y2="95" '
            f'stroke="{hexes["ETCHING"]}" stroke-width="1.5" '
            f'data-color-role="ETCHING"/>\n'
            f'      <text x="120" y="115" font-size="12" '
            f'fill="{hexes["ETCHING"]}" data-color-role="ETCHING">123</text>\n'
            f'      <line x1="120" y1="122" x2="190" y2="122" '
            f'stroke="{hexes["ETCHING_DEEP"]}" stroke-width="2.5" '
            f'data-color-role="ETCHING_DEEP"/>\n'
            f'      <line x1="10" y1="10" x2="30" y2="30" '
            f'stroke="{hexes["ANNOTATIONS"]}" stroke-width="1" '
            f'stroke-dasharray="3,2" data-color-role="ANNOTATIONS"/>\n'
            f'      <rect x="40" y="95" width="60" height="35" '
            f'fill="none" stroke="{hexes["SOLID_FILL"]}" stroke-width="2" '
            f'data-color-role="SOLID_FILL" data-fill-role="SOLID_FILL"/>\n'
            '    </svg>\n'
        )

    def serveColors(self, environ: object, start_response: object, lang: object) -> list[bytes]:
        """Render the /settings page (touch style)."""
        _ = lang.gettext  # type: ignore[attr-defined]
        lang_name = lang.info().get("language", None)  # type: ignore[attr-defined]
        langparam = f"?language={lang_name}" if lang_name else ""
        from boxes.Color import Color
        named_colors: list[tuple[str, str]] = [
            ("Black", "#000000"),
            ("White", "#ffffff"),
            ("Red", "#ff0000"),
            ("Green", "#00ff00"),
            ("Blue", "#0000ff"),
            ("Cyan", "#00ffff"),
            ("Magenta", "#ff00ff"),
            ("Yellow", "#ffff00"),
            ("Orange", "#ff8800"),
            ("Purple", "#8800ff"),
            ("Pink", "#ff00ff"),
            ("Gray", "#808080"),
            ("Light Gray", "#c0c0c0"),
            ("Brown", "#8b4513"),
            ("Lime", "#00ff00"),
            ("Navy", "#000080"),
            ("Olive", "#808000"),
            ("Teal", "#008080"),
            ("Maroon", "#800000"),
            ("Silver", "#c0c0c0"),
        ]

        # Helper to build a color control row
        def build_color_row(role: str) -> str:
            label, _ = Color.ROLE_LABELS[role]
            default_hex = Color.to_hex(getattr(Color, role))
            options = "\n".join(
                f'        <option value="{hex_val}"{" selected" if hex_val == default_hex else ""}>'
                f"{cname} ({hex_val})</option>"
                for cname, hex_val in named_colors
            )
            return (
                f'  <div class="cs-row">\n'
                f'    <div class="cs-label-swatch">\n'
                f'      <label for="color_{role}">{label}</label>\n'
                f'      <span class="color-swatch" style="background: {default_hex}"></span>\n'
                f'    </div>\n'
                f'    <select class="cs-select" id="color_{role}" data-role="{role}" onchange="onColorChange(this)">\n'
                f'{options}\n'
                f'    </select>\n'
                f'  </div>'
            )

        # Build columns: left, center (preview), right
        left_colors = "\n".join([
            build_color_row("OUTER_CUT"),
            build_color_row("INNER_CUT"),
            build_color_row("ANNOTATIONS"),
        ])
        right_colors = "\n".join([
            build_color_row("SOLID_FILL"),
            build_color_row("ETCHING"),
            build_color_row("ETCHING_DEEP"),
        ])

        preview_svg = self._colorPreviewSVG()
        touch_css = self.genHTMLTouchCSS()
        touch_js = self.genHTMLTouchJS()
        touch_header = self._touch_header_html(lang, back_url=f"TouchHub{langparam}", back_icon_only=True)
        page = (
            self.genHTMLStart(lang) + "\n"
            "<head>\n"
            f"  <title>{_('Colors')} \u2013 {_('Boxes.py')}</title>\n"
            f"  {self.genHTMLMeta()}\n"
            f"  {self.genHTMLThemeInit()}\n"
            f"  {self.genHTMLCSS()}\n"
            f"  {touch_css}\n"
            f"  {self.genHTMLColorsCSS()}\n"
            f"  {self.genHTMLJS()}\n"
            f"  {touch_js}\n"
            f"  {self.genHTMLShopJS()}\n"
            "</head>\n"
            f'<body class="touch-colors" onload="initColorSettingsPage()">\n'
            f"\n{touch_header}\n\n"
            '<div class="cs-body">\n'
            f"  <h2>{_('Colors')}</h2>\n"
            f"  <p>{_('Choose the SVG stroke color for each laser operation. Changes are saved instantly in your browser.')}</p>\n"
            '  <div class="cs-theme-section">\n'
            f"    <h3 style=\"margin:0;padding:0;width:auto;cursor:default;\">\U0001f3a8 {_('UI Theme')}</h3>\n"
            f"    <p style=\"margin:0;color:var(--th-text-muted);font-size:.9em;\">{_('Pick a color theme for the whole interface (background, buttons, headers).')}</p>\n"
            '    <div class="cs-theme-row">\n'
            '      <select id="theme-select" class="cs-select" style="width:auto" onchange="onThemeChange(this)"></select>\n'
            f'      <span id="theme-settings-status" style="display:none">{_("Saved.")}</span>\n'
            f'      <button class="cs-btn secondary" onclick="resetThemeSettings()">{_("Reset to default")}</button>\n'
            '    </div>\n'
            '  </div>\n'
            f'  <label class="cs-toggle-label"><input type="checkbox" id="cs-show-fill" onchange="toggleShowFill()">'
            f" {_('Show filled areas in preview')}</label>\n"
            f'  <div class="cs-layout">\n'
            f'    <div class="cs-column">\n'
            f'{left_colors}\n'
            f'    </div>\n'
            f'    <div class="cs-preview-column">\n'
            f'      <div class="cs-label-swatch">\n'
            f"        <label>{_('Live preview')}</label>\n"
            f'      </div>\n'
            f'      <div class="cs-preview">\n{preview_svg}\n      </div>\n'
            f'    </div>\n'
            f'    <div class="cs-column">\n'
            f'{right_colors}\n'
            f'    </div>\n'
            f'  </div>\n'
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
