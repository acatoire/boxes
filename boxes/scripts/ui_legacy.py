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

import boxes
from boxes.scripts.ui_shared import gen_interface_select_html


class LegacyUIMixin:
    """HTML generation for the classic (legacy) web interface.

    Designed as a mixin for BServer.  All methods use ``self`` attributes
    set by BServer.__init__ (static_url, groups, _cache, â€¦).
    """

    # â”€â”€ Stubs for attributes provided by BServer â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    static_url: str
    groups: list
    groups_by_name: dict
    _cache: dict
    _languages: list | None
    legal_url: str
    deploy_fingerprint: str
    ui_mode: str

    # â”€â”€ Shared helpers expected from BServer â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    def getLanguages(self) -> list:
        raise NotImplementedError

    # genHTMLTouchCSS / genHTMLTouchJS / _touch_header_html are provided
    # by TouchUIMixin at runtime â€“ do NOT redefine them here.

    def genHTMLStart(self, lang: object) -> str:
        lang_attr = lang.info().get("language", "")  # type: ignore[attr-defined]
        if lang_attr:
            return f'<!DOCTYPE html><html lang="{lang_attr.replace("_", "-")}">'
        return "<!DOCTYPE html><html>"

    def genHTMLMeta(self) -> str:
        return f"""
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link rel="icon" type="image/svg+xml" href="{self.static_url}/boxes-logo.svg" sizes="any">
    <link rel="icon" type="image/x-icon" href="{self.static_url}/favicon.ico">
"""

    def genHTMLMetaLanguageLink(self) -> str:
        """Generates meta language list for search engines."""
        s = ""
        for language in self.getLanguages():
            s += (
                f'    <link rel="alternate" hreflang="{language.replace("_", "-")}" '
                f'href="https://boxes.hackerspace-bamberg.de/?language={language}">\n'
            )
        return s

    def genHTMLCSS(self) -> str:
        return f'<link rel="stylesheet" href="{self.static_url}/self.css">'

    def genHTMLJS(self) -> str:
        return f'<script src="static/self.js"></script>'

    def genHTMLLanguageSelection(self, lang: object) -> str:
        """Generates a dropdown selection for language change."""
        current_language = lang.info().get("language", "")  # type: ignore[attr-defined]
        languages = self.getLanguages()
        if len(languages) < 2:
            return "<!-- No other languages to select found. -->"
        html_option = ""
        for language in languages:
            sel = " selected" if language == current_language else ""
            html_option += f"\t\t\t\t<option value='{language}'{sel}>{language}</option>\n"
        return (
            "\n        <form>\n"
            '            <select name="language" onchange=\'if(this.value != \\"'
            + current_language
            + '\\") { this.form.submit(); }\'>\n'
            + html_option
            + "            </select>\n        </form>\n"
        )

    def genHTMLColsSelection(self) -> str:
        """Zoom buttons for gallery image height."""
        return (
            '<button onclick="galleryZoomOut()" title="Smaller thumbnails" '
            'style="font-size:1em;padding:1px 7px;cursor:pointer;border:1px solid #999;'
            'border-radius:4px;background:#EFE8DA;">ðŸ”âˆ’</button>'
            '<button onclick="galleryZoomIn()" title="Larger thumbnails" '
            'style="font-size:1em;padding:1px 7px;cursor:pointer;border:1px solid #999;'
            'border-radius:4px;background:#EFE8DA;">ðŸ”+</button>'
        )

    def genPagePartHeader(self, lang: object, current_interface: str = "") -> str:
        _ = lang.gettext  # type: ignore[attr-defined]
        lang_name = lang.info().get("language", None)  # type: ignore[attr-defined]
        langparam = f"?language={lang_name}" if lang_name else ""
        return f"""
<h1><a href="./{langparam}">{_("Boxes.py")}</a></h1>
<p>{_("Create boxes and more with a laser cutter!")}</p>
<p>
{_('''        <a href="https://hackaday.io/project/10649-boxespy">Boxes.py</a> is an <a href="https://www.gnu.org/licenses/gpl-3.0.en.html">Open Source</a> box generator written in <a href="https://www.python.org/">Python</a>. It features both finished parametrized generators as well as a Python API for writing your own. It features finger and (flat) dovetail joints, flex cuts, holes and slots for screws, hinges, gears, pulleys and much more.''')}
</p>
</div>

<div style="width: 25%; float: left;">
<img alt="self-Logo" src="{self.static_url}/boxes-logo.svg" width="250">
</div>

<div>

<div class="clear"></div>
<hr/>
<div class="linkbar">
<ul>
{self.genLinks(lang, current_interface=current_interface)}
  <li class="right">\U0001f50d <input autocomplete="off" type="search" oninput="filterSearchItems();" name="search" id="search" placeholder="Search"></li>
</ul>
</div>
<hr/>
"""

    def genLinks(self, lang: object, preview: bool = False, current_interface: str = "") -> str:
        _ = lang.gettext  # type: ignore[attr-defined]
        links = [
            ("https://florianfesti.github.io/boxes/html/usermanual.html", _("Help")),
            ("https://hackaday.io/project/10649-boxespy", _("Home Page")),
            ("https://florianfesti.github.io/boxes/html/index.html", _("Documentation")),
            ("https://github.com/florianfesti/boxes", _("Sources")),
        ]
        if self.legal_url:
            links.append((self.legal_url, _("Legal")))
        links.append(("https://florianfesti.github.io/boxes/html/give_back.html", _("Give Back")))

        dropdown_items = [f'    <a href="{url}" target="_blank" rel="noopener">{txt}</a>\n' for url, txt in links]
        # Interface switcher
        dropdown_items.append(
            "    " + gen_interface_select_html(current_interface, _) + "\n"
        )
        dropdown_items.append(f'    <a href="colors">\U0001f3a8 {_("Colors")}</a>\n')
        dropdown_items.append(f'    <a href="categories">\U0001f4c2 {_("Categories")}</a>\n')
        # Language selection inside the dropdown
        lang_sel = self.genHTMLLanguageSelection(lang)
        if "select" in lang_sel:
            dropdown_items.append(
                f'    <div class="dropdown-lang">\U0001f310 {_("Language:")} {lang_sel}</div>\n'
            )
        dropdown_html = "".join(dropdown_items)

        result = [
            f'  <li class="dropdown">\n'
            f'    <button class="dropdown-btn" onclick="toggleDropdown(event)">\u2630 {_("Menu")}</button>\n'
            f'    <div class="dropdown-content" id="main-dropdown">\n'
            f'{dropdown_html}    </div>\n'
            f"  </li>\n"
        ]

        if self.deploy_fingerprint:
            tag = html.escape(self.deploy_fingerprint)
            result.append(f'  <li class="right" title="Deployment fingerprint">Instance: {tag}</li>\n')
        result.append(f'  <li class="right">{self.genHTMLColsSelection()}  </li>\n')
        return "".join(result)

    # â”€â”€ Form argument rendering â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    def arg2html(self, a: argparse.Action, prefix: str | None, defaults: dict = {}, _=lambda s: s) -> str:
        name = a.option_strings[0].replace("-", "")
        if isinstance(a, argparse._HelpAction):
            return ""
        viewname = name
        if prefix and name.startswith(prefix + "_"):
            viewname = name[len(prefix) + 1:]

        default = defaults.get(name, None)
        help_html = "" if not a.help else markdown.markdown(_(a.help))
        help_btn = (
            f'<button type="button" class="stepper-btn help-btn"'
            f" onclick=\"openHelpModal('{name}_description')\">?</button>"
        ) if a.help else ""
        row_head = (
            f'<tr>'
            f'<td id="{name}_id"><label for="{name}">{_(viewname)}</label></td>'
            f"<td>"
        )
        row_tail = (
            f'{help_btn}</td>'
            f'<td id="{name}_description" style="display:none">{help_html}</td>'
            f"</tr>\n"
        )
        if isinstance(a, argparse._StoreAction) and hasattr(a.type, "html"):
            input_html = a.type.html(name, default or a.default, _)  # type: ignore[union-attr]
        elif a.type == str and "\n" in a.default:
            val = (default or a.default).split("\n")
            input_html = (
                '<textarea name="%s" id="%s" aria-labeledby="%s %s" cols="%s" rows="%s">%s</textarea>'
                % (
                    name,
                    name,
                    name + "_id",
                    name + "_description",
                    max(len(l) for l in val) + 10,
                    len(val) + 1,
                    default or a.default,
                )
            )
        elif a.choices:
            options = "\n".join(
                '    <option value="%s"%s>%s</option>'
                % (
                    e,
                    ' selected="selected"'
                    if (e == (default or a.default)) or (str(e) == str(default or a.default))
                    else "",
                    _(e),
                )
                for e in a.choices
            )
            input_html = (
                '<select name="{}" id="{}" aria-labeledby="{} {}" size="1">\n{}</select>\n'.format(
                    name, name, name + "_id", name + "_description", options
                )
            )
        else:
            input_html = (
                '<input name="%s" id="%s" aria-labeledby="%s %s" type="text" value="%s">'
                % (name, name, name + "_id", name + "_description", default or a.default)
            )

        return row_head + input_html + row_tail

    def args2html_cached(self, name: str, box: object, lang: object, action: str = "", defaults: dict = {}) -> list[bytes]:
        if defaults == {}:
            key = (name, lang.info().get("language", None), action)  # type: ignore[attr-defined]
            if key not in self._cache:
                self._cache[key] = list(self.args2html(name, box, lang, action, defaults))
            return self._cache[key]
        return list(self.args2html(name, box, lang, action, defaults))

    def args2html(self, name: str, box: object, lang: object, action: str = "", defaults: dict = {}):
        _ = lang.gettext  # type: ignore[attr-defined]
        lang_name = lang.info().get("language", None)  # type: ignore[attr-defined]
        langparam = f"?language={lang_name}" if lang_name else ""

        no_img_msg = _(
            'There is no image yet. Please donate an image of your project on '
            '<a href=&quot;https://github.com/florianfesti/boxes/issues/628&quot; '
            'target=&quot;_blank&quot; rel=&quot;noopener&quot;>GitHub</a>!'
        )
        desc_html = (
            markdown.markdown(_(box.description), extensions=["extra"])  # type: ignore[attr-defined]
            .replace('src="static/', f'src="{self.static_url}/')
        ) if box.description else ""  # type: ignore[attr-defined]

        num_hide = len(box.argparser._action_groups) - 3  # type: ignore[attr-defined]
        result = [f"""{self.genHTMLStart(lang)}
<head>
    <title>{_("%s - Boxes") % _(name)}</title>
    {self.genHTMLMeta()}
{self.genHTMLMetaLanguageLink()}
    {self.genHTMLCSS()}
    {self.genHTMLJS()}
</head>
<body onload="initArgsPage({num_hide})">

<div class="argumentcontainer">
<div style="float: left;">
<a href="./{langparam}"><h1>{_("Boxes.py")}</h1></a>
</div>
<div style="width: 120px; float: right;">
<img alt="self-Logo" src="{self.static_url}/boxes-logo.svg" width="120">
</div>
<div>
<div class="clear"></div>
<hr>
<div class="linkbar">
<ul>
{self.genLinks(lang, True)}
</ul>
</div>
<hr>

<h2 style="margin: 0px 0px 0px 20px;">{_(name)}</h2>
<p>{_(box.__doc__) if box.__doc__ else ""}</p>
<div class="tabnav">
  <button class="tabbtn active" onclick="switchTab(event,'description')">{_("Description")}</button>
  <button class="tabbtn" onclick="switchTab(event,'configuration')">{_("Configuration")}</button>
</div>

<div id="tab-description" class="tab-panel">
<div class="description">
{desc_html}<div>
<img style="width:100%;" src="{self.static_url}/samples/{box.__class__.__name__}.jpg" onerror="this.parentElement.innerHTML = '{no_img_msg}';" alt="Picture of box.">
</div>
</div>
</div>

<div id="tab-configuration" class="tab-panel" style="display:none">
<div class="config-layout">
<div class="config-form">
<form id="arguments" action="{action}" method="GET" rel="nofollow">
        """]
        groupid = 0
        for group in box.argparser._action_groups[3:] + box.argparser._action_groups[:3]:  # type: ignore[attr-defined]
            if not group._group_actions:
                continue
            if len(group._group_actions) == 1 and isinstance(group._group_actions[0], argparse._HelpAction):
                continue
            prefix = getattr(group, "prefix", None)
            result.append(
                f'<h3 id="h-{groupid}" data-id="{groupid}" role="button" '
                f'aria-expanded="true" tabindex="0" class="toggle open">'
                f"{_(group.title)}</h3>\n"
                f'<table role="presentation" id="{groupid}">\n'
            )
            for a in group._group_actions:
                if a.dest in ("input", "output"):
                    continue
                result.append(self.arg2html(a, prefix, defaults, _))
            result.append("</table>")
            groupid += 1

        result.append(f"""
<input type="hidden" name="language" id="language" value="{lang_name}">

<p>
    <button name="render" value="1" formtarget="_blank">{_("Generate")}</button>
    <button name="render" value="2" formtarget="_self">{_("Download")}</button>
    <button name="render" value="0" formtarget="_self">{_("Save to URL")}</button>
    <button name="render" value="3" formtarget="_blank">{_("QR Code")}</button>
</p>
</form>
</div>

<div id="preview" class="config-preview">
  <div id="preview_buttons">
    {_("Zoom: ")}
    <button type="button" onclick="preview_scale/=1.2; document.getElementById('preview_img').style.width = preview_scale + '%';">-</button>
    <button type="button" onclick="preview_scale*= 1.2; document.getElementById('preview_img').style.width = preview_scale + '%';" >+</button>
    <button type="button" onclick="preview_scale=100; document.getElementById('preview_img').style.width = preview_scale + '%';" >{_("Reset")}</button>
  </div>
<div style="overflow: auto;">
<figure id="preview_figure">
<img id="preview_img" style="width:100%" src="{self.static_url}/nothing.png">
</figure>
</div>
</div>

</div>
</div>
</div>
<div class="clear"></div>
<hr>
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
</html>
        """)
        return (s.encode("utf-8") for s in result)

    # â”€â”€ Page generators â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    # genPageMenu          â†’ ui_menu.py              (MenuUIMixin)
    # serveGallery         â†’ ui_gallery.py           (GalleryUIMixin)
    # serveSettings        â†’ pages/settings.py       (SettingsUIMixin)
    # serveCategorySettingsâ†’ pages/categories.py     (CategoriesUIMixin)

    def genPageError(self, name: str, e: Exception, lang: object) -> list[bytes]:
        """Generates an error page."""
        _ = lang.gettext  # type: ignore[attr-defined]
        h = f"""{self.genHTMLStart(lang)}
<head>
  <title>{_("Error generating %s") % _(name)}</title>
  {self.genHTMLMeta()}
  <meta name="robots" content="noindex">
</head>
<body>
<h1>{_("An error occurred!")}</h1>
"""
        for s in str(e).split("\n"):
            h += f"<p>{html.escape(s)}</p>\n"
        h += "</body></html>"
        return [h.encode("utf-8")]

    def genPageErrorSVG(self, name: str, e: Exception, lang: object) -> object:
        """Generates an SVG error page."""
        _ = lang.gettext  # type: ignore[attr-defined]
        box = boxes.Boxes()
        box.parseArgs(["--reference=0.0"])
        box.open()
        box.text(_("An error occurred!"))
        box.text(str(e), y=-20, fontsize=7)
        return box.close()

    # serveGallery â†’ ui_gallery.py (GalleryUIMixin)
