# Copyright (C) 2016-2017 Florian Festi
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
from __future__ import annotations
import html
class CategoriesUIMixin:
    """Mixin that renders the /categories (Categories) page in touch style."""
    static_url: str
    groups: list
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
    def serveCategorySettings(self, environ: object, start_response: object, lang: object) -> list[bytes]:
        """Render the /categories page."""
        _ = lang.gettext  # type: ignore[attr-defined]
        lang_name = lang.info().get("language", None)  # type: ignore[attr-defined]
        langparam = f"?language={lang_name}" if lang_name else ""
        cards: list[str] = []
        for nr, group in enumerate(self.groups):
            gen_count = len(group.generators)
            first_thumb = (
                f"{self.static_url}/samples/{group.generators[0].__name__}-thumb.jpg"
                if group.generators else f"{self.static_url}/nothing.png"
            )
            cards.append(
                f'  <label class="cat-card" for="cat_{nr}" '
                f'style="background-image:url(\'{html.escape(first_thumb)}\')">\n'
                f'    <div class="cat-card-overlay">\n'
                f'      <input type="checkbox" id="cat_{nr}" data-cat-id="{nr}"\n'
                f'             onchange="onCategoryCheckboxChange(this)" checked>\n'
                f'      <span class="cat-card-title">{html.escape(_(group.title))}</span>\n'
                f'      <span class="cat-card-count">{gen_count}</span>\n'
                f'    </div>\n'
                f'  </label>'
            )
        cards_html = "\n".join(cards)
        touch_css = self.genHTMLTouchCSS()
        touch_js = self.genHTMLTouchJS()
        touch_header = self._touch_header_html(lang, back_url=f"TouchHub{langparam}", back_icon_only=True)
        page = (
            self.genHTMLStart(lang) + "\n"
            "<head>\n"
            f"  <title>{_('Categories')} \u2013 {_('Boxes.py')}</title>\n"
            f"  {self.genHTMLMeta()}\n"
            f"  {self.genHTMLCSS()}\n"
            f"  {touch_css}\n"
            f"  {self.genHTMLJS()}\n"
            f"  {touch_js}\n"
            "  <style>\n"
            "    body.touch-cat{margin:0;padding:0;min-height:100dvh;display:flex;flex-direction:column;background:var(--th-page-bg);font-size:17px;}\n"
            "    .cat-body{flex:1;padding:20px 24px;overflow-y:auto;}\n"
            "    .cat-body h2{margin:0 0 6px;color:#333;}\n"
            "    .cat-body p{margin:0 0 18px;color:#666;font-size:.9em;}\n"
            "    .cat-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(160px,1fr));gap:12px;margin-bottom:24px;}\n"
            "    .cat-card{position:relative;border-radius:10px;box-shadow:0 2px 8px rgba(0,0,0,.18);cursor:pointer;user-select:none;overflow:hidden;aspect-ratio:1/1;background-size:cover;background-position:center;background-color:#d8d0c0;transition:transform .12s,box-shadow .12s;}\n"
            "    .cat-card:hover{transform:scale(1.03);box-shadow:0 6px 20px rgba(0,0,0,.28);}\n"
            "    .cat-card:active{transform:scale(0.97);}\n"
            "    .cat-card-overlay{position:absolute;inset:0;background:linear-gradient(to bottom,rgba(0,0,0,.05) 40%,rgba(0,0,0,.72) 100%);display:flex;flex-direction:column;justify-content:flex-end;padding:10px;gap:4px;}\n"
            "    .cat-card input[type='checkbox']{position:absolute;top:10px;right:10px;width:24px;height:24px;cursor:pointer;accent-color:var(--th-accent);}\n"
            "    .cat-card-title{font-weight:bold;font-size:.92em;color:#fff;text-shadow:0 1px 3px rgba(0,0,0,.8);line-height:1.2;}\n"
            "    .cat-card-count{font-size:.75em;color:rgba(255,255,255,.80);text-shadow:0 1px 2px rgba(0,0,0,.7);}\n"
            "    .cat-actions{display:flex;gap:12px;flex-wrap:wrap;align-items:center;}\n"
            "    .cat-btn{background:var(--th-accent);color:#fff;border:none;border-radius:10px;padding:0 24px;min-height:48px;font-size:1em;font-family:inherit;font-weight:bold;cursor:pointer;transition:background .15s;}\n"
            "    .cat-btn:hover{background:var(--th-accent2);}\n"
            "    .cat-btn.secondary{background:#666;}\n"
            "    .cat-btn.secondary:hover{background:#444;}\n"
            "    #cat-settings-status{color:green;font-weight:bold;}\n"
            "  </style>\n"
            "</head>\n"
            f'<body class="touch-cat" onload="initCategorySettingsPage()">\n'
            f"\n{touch_header}\n\n"
            '<div class="cat-body">\n'
            f"  <h2>{_('Categories')}</h2>\n"
            f"  <p>{_('Uncheck categories to hide them from the menu, gallery and touch interface.')}</p>\n"
            '  <div class="cat-grid">\n'
            f"{cards_html}\n"
            "  </div>\n"
            '  <div class="cat-actions">\n'
            f'    <button class="cat-btn" onclick="saveCategorySettingsExplicit()">{_("Save")}</button>\n'
            f'    <button class="cat-btn secondary" onclick="resetCategorySettings()">{_("Show all categories")}</button>\n'
            f'    <span id="cat-settings-status" style="display:none">{_("Saved.")}</span>\n'
            "  </div>\n"
            "</div>\n\n</body>\n</html>\n"
        )
        start_response("200 OK", [("Content-type", "text/html; charset=utf-8")])  # type: ignore[operator]
        return [page.encode("utf-8")]
