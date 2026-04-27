# Copyright (C) 2016-2017 Florian Festi
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
from __future__ import annotations

import argparse
import html

import markdown


class TouchUIMixin:
    """HTML generation for the touch / tablet interface.

    Designed as a mixin for BServer.  All methods use ``self`` attributes
    set by BServer.__init__ (static_url, groups, _cache, …).
    """

    # ── Stubs for attributes provided by BServer ─────────────────────
    static_url: str
    groups: list
    _cache: dict
    legal_url: str
    deploy_fingerprint: str

    # ── Shared helpers expected from LegacyUIMixin / BServer ─────────
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

    def genHTMLLanguageSelection(self, lang: object) -> str:
        raise NotImplementedError

    def tag_badges_html(self, box: type) -> str:
        raise NotImplementedError

    def arg2html(self, a: argparse.Action, prefix: str | None, defaults: dict = {}, _ = lambda s: s) -> str:
        raise NotImplementedError

    # ── Touch-specific assets ─────────────────────────────────────────

    def genHTMLTouchCSS(self) -> str:
        return f'<link rel="stylesheet" href="{self.static_url}/touch.css">'

    def genHTMLTouchJS(self) -> str:
        return f'<script src="{self.static_url}/touch.js"></script>'

    # ── Shared header bar ─────────────────────────────────────────────

    def _touch_header_html(self, lang: object, back_url: str = "") -> str:
        """Sticky header bar rendered on every touch page."""
        _ = lang.gettext  # type: ignore[attr-defined]
        lang_name = lang.info().get("language", None)  # type: ignore[attr-defined]
        langparam = f"?language={lang_name}" if lang_name else ""

        back_btn = (
            f'<a class="th-mode-btn" href="{html.escape(back_url)}" '
            f'aria-label="{_("Back")}">← {_("Back")}</a>'
            if back_url
            else ""
        )

        # Build the ☰ dropdown menu (mirrors legacy genLinks dropdown)
        links: list[tuple[str, str]] = [
            ("https://florianfesti.github.io/boxes/html/usermanual.html", _("Help")),
            ("https://hackaday.io/project/10649-boxespy", _("Home Page")),
            ("https://florianfesti.github.io/boxes/html/index.html", _("Documentation")),
            ("https://github.com/florianfesti/boxes", _("Sources")),
        ]
        if self.legal_url:
            links.append((self.legal_url, _("Legal")))
        links.append(("https://florianfesti.github.io/boxes/html/give_back.html", _("Give Back")))

        dropdown_items: list[str] = [
            f'      <a href="{url}" target="_blank" rel="noopener">{txt}</a>'
            for url, txt in links
        ]
        dropdown_items.append(
            f'      <a href="Gallery" onclick="try{{localStorage.setItem(\'boxes-ui-mode\',\'legacy\')}}catch(e){{}}">'
            f'\U0001f5bc\ufe0f {_("Gallery interface")}</a>'
        )
        dropdown_items.append(
            f'      <a href="Menu" onclick="try{{localStorage.setItem(\'boxes-ui-mode\',\'legacy\')}}catch(e){{}}">'
            f'\U0001f4cb {_("Menu interface")}</a>'
        )
        dropdown_items.append(
            f'      <a href="TouchHub" onclick="try{{localStorage.setItem(\'boxes-ui-mode\',\'touch\')}}catch(e){{}}">'
            f'\U0001f4f1 {_("Touch interface")}</a>'
        )
        dropdown_items.append(f'      <a href="settings">\U0001f3a8 {_("Color Settings")}</a>')
        dropdown_items.append(f'      <a href="categories">\U0001f4c2 {_("Category Settings")}</a>')
        # Language selection inside the dropdown
        lang_sel = self.genHTMLLanguageSelection(lang)
        if "select" in lang_sel:
            dropdown_items.append(
                f'      <div class="dropdown-lang">\U0001f310 {_("Language:")} {lang_sel}</div>'
            )
        if self.deploy_fingerprint:
            tag = html.escape(self.deploy_fingerprint)
            dropdown_items.append(
                f'      <span style="padding:6px 12px;color:#aaa;font-size:0.8em;">Instance: {tag}</span>'
            )

        dropdown_html = "\n".join(dropdown_items)

        return f"""
  <header class="th-header">
    <a class="th-logo" href="TouchHub{langparam}">
      <img src="{self.static_url}/boxes-logo.svg" alt="Boxes.py" height="40">
      <span class="th-logo-text">{_("Boxes.py")}</span>
    </a>
    <div class="th-header-actions">
      {back_btn}
      <div class="dropdown th-dropdown">
        <button class="th-mode-btn dropdown-btn" onclick="toggleDropdown(event)">\u2630 {_("Menu")}</button>
        <div class="dropdown-content th-dropdown-content" id="main-dropdown">
{dropdown_html}
        </div>
      </div>
    </div>
  </header>"""

    # ── Hub page ─────────────────────────────────────────────────────

    def genTouchHub(self, lang: object) -> list[bytes]:
        """Generate the full tabbed touch-mode hub page."""
        _ = lang.gettext  # type: ignore[attr-defined]
        lang_name = lang.info().get("language", None)  # type: ignore[attr-defined]
        langparam = f"?language={lang_name}" if lang_name else ""

        tabs_html: list[str] = []
        panels_html: list[str] = []

        for nr, group in enumerate(self.groups):
            gen_count = len(group.generators)
            is_first = nr == 0
            active_cls = "active" if is_first else ""
            tabs_html.append(
                f'<button class="th-tab {active_cls}" role="tab" '
                f'aria-selected="{str(is_first).lower()}" '
                f'data-group="{nr}" onclick="thSwitchTab({nr})" '
                f'title="{html.escape(_(group.title))}">'
                f'<span class="th-tab-label">{html.escape(_(group.title))}</span>'
                f'<span class="th-tab-count">{gen_count}</span>'
                f"</button>"
            )

            cards: list[str] = []
            for box in group.generators:
                bname = box.__name__
                doc = html.escape(_(box.__doc__) if box.__doc__ else "")
                thumb = f"{self.static_url}/samples/{bname}-thumb.jpg"
                badges = self.tag_badges_html(box)
                href = f"{bname}{langparam}"
                cards.append(
                    f'<a class="th-card" href="{html.escape(href)}" '
                    f'id="tc_{bname}" title="{html.escape(_(bname))}">'
                    f'<img class="th-card-thumb" src="{thumb}" '
                    f'alt="{html.escape(_(bname))}" loading="lazy" '
                    f"onerror=\"this.outerHTML='<div class=&quot;th-card-thumb-missing&quot;>📦</div>'\">"
                    f'<div class="th-card-info">'
                    f'<span class="th-card-name">{html.escape(_(bname))}{badges}</span>'
                    f'<span class="th-card-doc">{doc}</span>'
                    f"</div></a>"
                )

            display = "block" if is_first else "none"
            panels_html.append(
                f'<div class="th-panel {active_cls}" data-group="{nr}" '
                f'id="th-panel-{nr}" role="tabpanel" style="display:{display}">'
                f'<div class="th-grid">{"".join(cards)}</div>'
                f"</div>"
            )

        page = f"""{self.genHTMLStart(lang)}
<head>
  <title>{_("Boxes.py")}</title>
  {self.genHTMLMeta()}
{self.genHTMLMetaLanguageLink()}
  {self.genHTMLCSS()}
  {self.genHTMLTouchCSS()}
  {self.genHTMLJS()}
  {self.genHTMLTouchJS()}
</head>
<body class="touch-hub" onload="initTouchHub()">

{self._touch_header_html(lang)}

  <nav class="th-tabbar" role="tablist" aria-label="{_("Generator categories")}">
    {"".join(tabs_html)}
  </nav>

  <main class="th-content" id="th-content">
    {"".join(panels_html)}
  </main>

</body>
</html>"""
        return [page.encode("utf-8")]

    # ── Generator config page ──────────────────────────────────────────

    def genTouchArgs(
        self,
        name: str,
        box: object,
        lang: object,
        action: str = "",
        defaults: dict = {},
    ) -> list[bytes]:
        """Touch-mode generator configuration page."""
        _ = lang.gettext  # type: ignore[attr-defined]
        lang_name = lang.info().get("language", None)  # type: ignore[attr-defined]
        langparam = f"?language={lang_name}" if lang_name else ""

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
            if len(group._group_actions) == 1 and isinstance(group._group_actions[0], argparse._HelpAction):
                continue
            prefix = getattr(group, "prefix", None)
            form_rows.append(
                f'<h3 id="h-{groupid}" data-id="{groupid}" role="button" '
                f'aria-expanded="true" tabindex="0" class="toggle open">'
                f"{_(group.title)}</h3>\n"
                f'<table role="presentation" id="{groupid}">\n'
            )
            for a in group._group_actions:
                if a.dest in ("input", "output"):
                    continue
                form_rows.append(self.arg2html(a, prefix, defaults, _))
            form_rows.append("</table>")
            groupid += 1

        num_hide = len(box.argparser._action_groups) - 3  # type: ignore[attr-defined]

        page = f"""{self.genHTMLStart(lang)}
<head>
  <title>{_("%s - Boxes") % _(name)}</title>
  {self.genHTMLMeta()}
{self.genHTMLMetaLanguageLink()}
  {self.genHTMLCSS()}
  {self.genHTMLTouchCSS()}
  {self.genHTMLJS()}
  {self.genHTMLTouchJS()}
</head>
<body class="touch-args" onload="initTouchArgs({num_hide})">

{self._touch_header_html(lang, back_url=f"TouchHub{langparam}")}

<div class="touch-args-body">

  <div class="touch-breadcrumb">
    <a href="TouchHub{langparam}">{_("Boxes.py")}</a>
    <span>›</span>
    <span>{_(name)}</span>
  </div>

  <p class="touch-gen-doc">{_(box.__doc__) if box.__doc__ else ""}</p>

  <div class="tabnav">
    <button class="tabbtn active" onclick="switchTab(event,'description')">{_("Description")}</button>
    <button class="tabbtn" onclick="switchTab(event,'configuration')">{_("Configuration")}</button>
  </div>

  <div id="tab-description" class="tab-panel">
    <div class="description">
      {desc_html}
      <div>
        <img style="width:100%;max-width:480px;" src="{self.static_url}/samples/{box.__class__.__name__}.jpg"
             onerror="this.parentElement.innerHTML = '{no_img_msg}';" alt="Picture of box.">
      </div>
    </div>
  </div>

  <div id="tab-configuration" class="tab-panel" style="display:none">
    <div class="config-layout">
      <div class="config-form">
        <form id="arguments" action="{action}" method="GET" rel="nofollow">
          {"".join(form_rows)}
          <input type="hidden" name="language" id="language" value="{lang_name}">
        </form>
      </div>
      <div id="preview" class="config-preview">
        <div id="preview_buttons">
          {_("Zoom: ")}
          <button type="button" onclick="preview_scale/=1.2; document.getElementById('preview_img').style.width = preview_scale + '%';">−</button>
          <button type="button" onclick="preview_scale*= 1.2; document.getElementById('preview_img').style.width = preview_scale + '%';">+</button>
          <button type="button" onclick="preview_scale=100; document.getElementById('preview_img').style.width = preview_scale + '%';">{_("Reset")}</button>
        </div>
        <div style="overflow:auto;">
          <figure id="preview_figure">
            <img id="preview_img" style="width:100%" src="{self.static_url}/nothing.png">
          </figure>
        </div>
      </div>
    </div>
  </div>

</div><!-- /touch-args-body -->

<!-- Sticky bottom action bar -->
<div class="touch-action-bar">
  <button class="touch-action-btn" data-render="1" data-target="_blank">{_("Generate")}</button>
  <button class="touch-action-btn secondary" data-render="2" data-target="_self">{_("Download")}</button>
  <button class="touch-action-btn secondary" data-render="0" data-target="_self">{_("Save URL")}</button>
  <button class="touch-action-btn secondary" data-render="3" data-target="_blank">{_("QR Code")}</button>
</div>

<!-- Help modal -->
<div id="help-modal" class="help-modal-overlay" onclick="closeHelpModal()">
  <div class="help-modal-box" onclick="event.stopPropagation()">
    <div id="help-modal-content" class="help-modal-content"></div>
    <button type="button" class="stepper-btn help-modal-close" onclick="closeHelpModal()">Close</button>
  </div>
</div>

<!-- Image modal -->
<div id="img-modal" class="img-modal-overlay" onclick="closeImgModal()">
  <img id="img-modal-img" src="" alt="">
</div>

</body>
</html>"""
        return [page.encode("utf-8")]

    # ── WSGI handler ─────────────────────────────────────────────────

    def serveTouchHub(self, environ: object, start_response: object, lang: object) -> list[bytes]:
        """Serve the touch-mode category hub page (with caching)."""
        lang_name = lang.info().get("language", None)  # type: ignore[attr-defined]
        cache_key = ("TouchHub", lang_name)

        start_response("200 OK", [  # type: ignore[operator]
            ("Content-type", "text/html; charset=utf-8"),
            ("X-XSS-Protection", "1; mode=block"),
            ("X-Content-Type-Options", "nosniff"),
            ("x-frame-options", "SAMEORIGIN"),
            ("Referrer-Policy", "no-referrer"),
        ])

        if cache_key not in self._cache:
            self._cache[cache_key] = self.genTouchHub(lang)
        return self._cache[cache_key]
