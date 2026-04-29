# Copyright (C) 2016-2017 Florian Festi
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
from __future__ import annotations
import argparse
import markdown
class GeneratorUIMixin:
    """Mixin that renders the touch-mode generator configuration page (/GeneratorName)."""
    static_url: str
    def genHTMLStart(self, lang: object) -> str:
        raise NotImplementedError
    def genHTMLMeta(self) -> str:
        raise NotImplementedError
    def genHTMLMetaLanguageLink(self) -> str:
        raise NotImplementedError
    def genHTMLCSS(self) -> str:
        raise NotImplementedError
    def genHTMLJS(self) -> str:
        raise NotImplementedError
    def genHTMLTouchCSS(self) -> str:
        raise NotImplementedError
    def genHTMLTouchJS(self) -> str:
        raise NotImplementedError
    def _touch_header_html(
        self,
        lang: object,
        back_url: str = "",
        back_icon_only: bool = False,
        center_html: str = "",
    ) -> str:
        raise NotImplementedError
    def arg2html(
        self,
        a: argparse.Action,
        prefix: str | None,
        defaults: dict | None = None,
        _=lambda s: s,
    ) -> str:
        raise NotImplementedError
    def tag_badges_html(self, box: type) -> str:
        raise NotImplementedError
    # Generator config page
    def genTouchArgs(
        self,
        name: str,
        box: object,
        lang: object,
        action: str = "",
        defaults: dict | None = None,
        back_url: str = "",
    ) -> list[bytes]:
        """Touch-mode generator configuration page."""
        _ = lang.gettext  # type: ignore[attr-defined]
        lang_name = lang.info().get("language", None)  # type: ignore[attr-defined]
        langparam = f"?language={lang_name}" if lang_name else ""
        resolved_back = back_url if back_url else f"TouchHub{langparam}"
        no_img_msg = _(
            "There is no image yet. Please donate an image of your project on "
            '<a href=&quot;https://github.com/florianfesti/boxes/issues/628&quot; '
            'target=&quot;_blank&quot; rel=&quot;noopener&quot;>GitHub</a>!'
        )
        desc_html = (
            markdown.markdown(_(box.description), extensions=["extra"])  # type: ignore[attr-defined]
            .replace('src="static/', f'src="{self.static_url}/')
        ) if box.description else ""  # type: ignore[attr-defined]
        form_rows: list[str] = []
        groupid = 0
        for group in box.argparser._action_groups[3:] + box.argparser._action_groups[:3]:  # type: ignore[attr-defined]
            if not group._group_actions:
                continue
            if len(group._group_actions) == 1 and isinstance(
                group._group_actions[0], argparse._HelpAction
            ):
                continue
            prefix = getattr(group, "prefix", None)
            form_rows.append(
                f'<h3 id="h-{groupid}" data-id="{groupid}" role="button" '
                f'aria-expanded="true" tabindex="0" class="toggle open">'
                f"{_(group.title)}</h3>\n"
                f'<table role="presentation" id="{groupid}">\n'
            )
            for a in group._group_actions:
                if a.dest in ("input", "output", "language"):
                    continue
                form_rows.append(self.arg2html(a, prefix, defaults, _))
            form_rows.append("</table>")
            groupid += 1
        num_hide = len(box.argparser._action_groups) - 3  # type: ignore[attr-defined]
        # Tab buttons go in the header center
        tabs_html = (
            f'<button class="tabbtn th-tab-btn active" onclick="switchTab(event,\'description\')">'
            f'{_("Description")}</button>'
            f'<button class="tabbtn th-tab-btn" onclick="switchTab(event,\'configuration\')">'
            f'{_("Configuration")}</button>'
        )
        header_html = self._touch_header_html(
            lang, back_url=resolved_back, back_icon_only=True, center_html=tabs_html
        )
        page = (
            self.genHTMLStart(lang) + "\n"
            "<head>\n"
            f"  <title>{_('%s - Boxes') % _(name)}</title>\n"
            f"  {self.genHTMLMeta()}\n"
            f"{self.genHTMLMetaLanguageLink()}\n"
            f"  {self.genHTMLCSS()}\n"
            f"  {self.genHTMLTouchCSS()}\n"
            f"  {self.genHTMLJS()}\n"
            f"  {self.genHTMLTouchJS()}\n"
            f'  <script src="{self.static_url}/generator.js"></script>\n'
            "</head>\n"
            f'<body class="touch-args" onload="initTouchArgs({num_hide})">\n'
            f"\n{header_html}\n\n"
            '<div class="touch-args-body">\n'
            f'  <p class="touch-gen-doc">{_(box.__doc__) if box.__doc__ else ""}</p>\n'
            f'  <div id="tab-description" class="tab-panel">\n'
            "    <div class=\"description\">\n"
            f"      {desc_html}\n"
            "      <div>\n"
            f'        <img style="width:100%;max-width:480px;" src="{self.static_url}/samples/{box.__class__.__name__}.jpg"\n'
            f"             onerror=\"this.parentElement.innerHTML = '{no_img_msg}';\" alt=\"Picture of box.\">\n"
            "      </div>\n"
            "    </div>\n"
            "  </div>\n"
            '\n  <div id="tab-configuration" class="tab-panel" style="display:none">\n'
            '    <div class="config-layout">\n'
            '      <div class="config-form">\n'
            f'        <form id="arguments" action="{action}" method="GET" rel="nofollow">\n'
            f'          {"".join(form_rows)}\n'
            f'          <input type="hidden" name="language" id="language" value="{lang_name or ""}">\n'
            "        </form>\n"
            "      </div>\n"
            '      <div id="preview" class="config-preview">\n'
            '        <div class="preview-controls">\n'
            '          <div id="preview_buttons" class="preview-ctrl-card">\n'
            f'            {_("Zoom: ")}\n'
            '            <button type="button" onclick="preview_scale/=1.2; document.getElementById(\'preview_img\').style.width = preview_scale + \'%\';">\u2212</button>\n'
            '            <button type="button" onclick="preview_scale*= 1.2; document.getElementById(\'preview_img\').style.width = preview_scale + \'%\';">+</button>\n'
            f'            <button type="button" onclick="preview_scale=100; document.getElementById(\'preview_img\').style.width = preview_scale + \'%\';">{_("Reset")}</button>\n'
            "          </div>\n"
            '          <div id="surface-info-bar" class="surface-info-bar"></div>\n'
            '          <div id="fit-info-bar" class="fit-info"></div>\n'
            "        </div>\n"
            '        <div style="overflow:auto;">\n'
            '          <figure id="preview_figure">\n'
            f'            <img id="preview_img" style="width:100%" src="{self.static_url}/nothing.png">\n'
            "          </figure>\n"
            "        </div>\n"
            "      </div>\n"
            "    </div>\n"
            "  </div>\n"
            "\n</div><!-- /touch-args-body -->\n"
            "\n<!-- Sticky bottom action bar -->\n"
            '<div class="touch-action-bar">\n'
            f'  <button class="touch-action-btn" data-render="1" data-target="_blank">{_("Generate")}</button>\n'
            f'  <button class="touch-action-btn secondary" data-render="2" data-target="_self">{_("Download")}</button>\n'
            f'  <button class="touch-action-btn secondary" data-render="0" data-target="_self">{_("URL")}</button>\n'
            f'  <button class="touch-action-btn secondary" data-render="3" data-target="_blank">{_("QR")}</button>\n'
            f'  <button class="touch-action-btn secondary" type="button" onclick="saveParamsAsJson()">{_("Save")}</button>\n'
            f'  <label class="touch-action-btn secondary" style="cursor:pointer;">{_("Import")}'
            f'<input type="file" accept=".json" style="display:none" onchange="loadParamsFromJson(this)"></label>\n'
            "</div>\n"
            "\n<!-- Help modal -->\n"
            '<div id="help-modal" class="help-modal-overlay" onclick="closeHelpModal()">\n'
            '  <div class="help-modal-box" onclick="event.stopPropagation()">\n'
            '    <div id="help-modal-content" class="help-modal-content"></div>\n'
            '    <button type="button" class="stepper-btn help-modal-close" onclick="closeHelpModal()">Close</button>\n'
            "  </div>\n"
            "</div>\n"
            "\n<!-- Image modal -->\n"
            '<div id="img-modal" class="img-modal-overlay" onclick="closeImgModal()">\n'
            '  <img id="img-modal-img" src="" alt="">\n'
            "</div>\n"
            "\n</body>\n</html>\n"
        )
        return [page.encode("utf-8")]
