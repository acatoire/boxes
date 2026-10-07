# Copyright (C) 2025
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


class HideConfigUIMixin:
    """Mixin that renders the /hideconfig (Hide Configuration) help page."""

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

    def genHTMLShopJS(self) -> str:
        raise NotImplementedError

    def genHTMLThemeInit(self) -> str:
        raise NotImplementedError

    def genHTMLHideConfigCSS(self) -> str:
        raise NotImplementedError

    def _touch_header_html(
        self,
        lang: object,
        back_url: str = "",
        back_icon_only: bool = False,
        center_html: str = "",
        show_dropdown: bool = True,
    ) -> str:
        raise NotImplementedError

    def serveHideConfig(
        self, environ: object, start_response: object, lang: object
    ) -> list[bytes]:
        """Render the /hideconfig (Hide Configuration) help page."""
        _ = lang.gettext  # type: ignore[attr-defined]
        lang_name = lang.info().get("language", None)  # type: ignore[attr-defined]
        langparam = f"?language={lang_name}" if lang_name else ""

        touch_header = self._touch_header_html(
            lang, back_url=f"TouchHub{langparam}", back_icon_only=True
        )

        secret_text = _("Click on the \"Language:\" label 10 times in quick succession.")

        page = (
            self.genHTMLStart(lang)
            + "\n"
            "<head>\n"
            f"  <title>{_('Hide Configuration')} \u2013 {_('Boxes.py')}</title>\n"
            f"  {self.genHTMLMeta()}\n"
            f"  {self.genHTMLThemeInit()}\n"
            f"  {self.genHTMLCSS()}\n"
            f"  {self.genHTMLTouchCSS()}\n"
            f"  {self.genHTMLHideConfigCSS()}\n"
            f"  {self.genHTMLJS()}\n"
            f"  {self.genHTMLTouchJS()}\n"
            f"  {self.genHTMLShopJS()}\n"
            "</head>\n"
            f'<body class="touch-hideconfig">\n'
            f"\n{touch_header}\n\n"
            '<div class="hc-body">\n'
            f"  <h2>🔧 {_('Hide Configuration')}</h2>\n"
            f"  <div class=\"hc-content\">\n"
            f"    <h3>{_('What is this page?')}</h3>\n"
            f"    <p>{_('When you select a shop, some configuration options are hidden from the menu to simplify the experience for customers. This includes:')}</p>\n"
            f"    <ul>\n"
            f"      <li>{_('Colors page')}</li>\n"
            f"      <li>{_('Machine settings (including margin coefficient)')}</li>\n"
            f"      <li>{_('Selection/Categories menu')}</li>\n"
            f"      <li>{_('Shop selection dropdown')}</li>\n"
            f"    </ul>\n"
            f"    <p>{_('This streamlined view helps customers focus on creating their designs without being overwhelmed by technical settings.')}</p>\n"
            f"    <h3>{_('How to unhide the menu')}</h3>\n"
            f"    <p>{_('If you need to access the hidden configuration options, use the secret action:')}</p>\n"
            '    <div class="hc-secret">\n'
            f"      <strong>{secret_text}</strong>\n"
            "    </div>\n"
            f"    <p>{_('This will return you to the full menu with all configuration options visible.')}</p>\n"
            "  </div>\n"
            "  <div class=\"hc-actions\">\n"
            f'    <button class="hc-btn" onclick="reactivateHiddenFeatures()">{_("Re-activate hidden feature")}</button>\n'
            "  </div>\n"
            "</div>\n\n"
            "</body>\n</html>\n"
        )
        start_response("200 OK", [("Content-type", "text/html; charset=utf-8")])  # type: ignore[operator]
        return [page.encode("utf-8")]
