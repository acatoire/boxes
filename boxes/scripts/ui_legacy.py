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
    set by BServer.__init__ (static_url, groups, _cache, …).
    """

    # ── Stubs for attributes provided by BServer ─────────────────────
    static_url: str
    groups: list
    groups_by_name: dict
    _cache: dict
    _languages: list | None
    legal_url: str
    deploy_fingerprint: str
    ui_mode: str

    # ── Shared helpers expected from BServer ─────────────────────────
    def getLanguages(self) -> list:
        raise NotImplementedError

    # genHTMLTouchCSS / genHTMLTouchJS / _touch_header_html are provided
    # by TouchUIMixin at runtime – do NOT redefine them here.

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
            'border-radius:4px;background:#EFE8DA;">🔍−</button>'
            '<button onclick="galleryZoomIn()" title="Larger thumbnails" '
            'style="font-size:1em;padding:1px 7px;cursor:pointer;border:1px solid #999;'
            'border-radius:4px;background:#EFE8DA;">🔍+</button>'
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
        dropdown_items.append(f'    <a href="settings">\U0001f3a8 {_("Color Settings")}</a>\n')
        dropdown_items.append(f'    <a href="categories">\U0001f4c2 {_("Category Settings")}</a>\n')
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

    # ── Form argument rendering ──────────────────────────────────────

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

    # ── Page generators ──────────────────────────────────────────────
    # genPageMenu  → ui_menu.py    (MenuUIMixin)
    # serveGallery → ui_gallery.py (GalleryUIMixin)

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

    def serveSettings(self, environ: object, start_response: object, lang: object) -> list[bytes]:
        """Render the /settings page."""
        _ = lang.gettext  # type: ignore[attr-defined]
        from boxes.Color import Color

        named_colors: list[tuple[str, str]] = [
            (cname, Color.to_hex(getattr(Color, cname)))
            for cname in ("BLACK", "BLUE", "GREEN", "RED", "CYAN", "YELLOW", "MAGENTA", "WHITE")
        ]
        rows = []
        for role, (label, desc) in Color.ROLE_LABELS.items():
            default_hex = Color.to_hex(getattr(Color, role))
            options = "\n".join(
                f'      <option value="{hex_val}"{" selected" if hex_val == default_hex else ""}>'
                f"{cname} ({hex_val})</option>"
                for cname, hex_val in named_colors
            )
            rows.append(f"""
  <tr>
    <td><label for="color_{role}">{label}</label></td>
    <td>
      <select id="color_{role}" data-role="{role}" onchange="onColorChange(this)">
{options}
      </select>
    </td>
    <td class="color-desc">{desc}</td>
  </tr>""")

        rows_html = "\n".join(rows)
        page = f"""{self.genHTMLStart(lang)}
<head>
  <title>{_("Color Settings")} \u2013 {_("Boxes.py")}</title>
  {self.genHTMLMeta()}
  {self.genHTMLCSS()}
  {self.genHTMLJS()}
  <style>
    .color-settings-table {{ border-collapse: collapse; width: 100%; max-width: 760px; }}
    .color-settings-table td {{ padding: 8px 12px; vertical-align: middle; }}
    .color-settings-table select {{ padding: 4px 6px; border: 1px solid #ccc; border-radius: 4px; }}
    .color-swatch {{ display: inline-block; width: 18px; height: 18px; border-radius: 3px; border: 1px solid #888; vertical-align: middle; margin-left: 6px; }}
    .color-desc {{ color: #555; font-size: 0.9em; }}
    .settings-actions {{ margin-top: 16px; display: flex; gap: 12px; align-items: center; }}
    #import-file {{ display: none; }}
  </style>
</head>
<body onload="initColorSettingsPage()">
<div class="container">
<div style="width:75%; float:left;">
{self.genPagePartHeader(lang)}
<h2>{_("Color Settings")}</h2>
<p>{_("Choose the SVG stroke color for each laser operation. Changes are saved instantly in your browser.")}</p>
<table class="color-settings-table">
  <thead><tr>
    <th>{_("Role")}</th>
    <th>{_("Color")}</th>
    <th>{_("Description")}</th>
  </tr></thead>
  <tbody>
{rows_html}
  </tbody>
</table>
<div class="settings-actions">
  <button onclick="saveColorSettingsExplicit()">{_("Save")}</button>
  <button onclick="exportColorSettings()">{_("Export JSON")}</button>
  <button onclick="document.getElementById('import-file').click()">{_("Import JSON")}</button>
  <input type="file" id="import-file" accept=".json,application/json" onchange="importColorSettings(this)">
  <button onclick="resetColorSettings()">{_("Reset to defaults")}</button>
  <span id="color-settings-status" style="color:green; display:none">{_("Saved.")}</span>
</div>
</div>
<div style="width:5%; float:left;"></div>
<div class="clear"></div><hr>
</div>
</body>
</html>
"""
        start_response("200 OK", [("Content-type", "text/html; charset=utf-8")])  # type: ignore[operator]
        return [page.encode("utf-8")]

    def serveCategorySettings(self, environ: object, start_response: object, lang: object) -> list[bytes]:
        """Render the /categories page – checkbox per generator category (touch style)."""
        _ = lang.gettext  # type: ignore[attr-defined]
        lang_name = lang.info().get("language", None)  # type: ignore[attr-defined]
        langparam = f"?language={lang_name}" if lang_name else ""

        cards: list[str] = []
        for nr, group in enumerate(self.groups):
            gen_count = len(group.generators)
            # Use the first generator's thumbnail as card background
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
        touch_css = self.genHTMLTouchCSS()  # type: ignore[attr-defined]
        touch_js = self.genHTMLTouchJS()  # type: ignore[attr-defined]
        touch_header = self._touch_header_html(lang, back_url=f"TouchHub{langparam}")  # type: ignore[attr-defined]
        page = f"""{self.genHTMLStart(lang)}
<head>
  <title>{_("Category Settings")} \u2013 {_("Boxes.py")}</title>
  {self.genHTMLMeta()}
  {self.genHTMLCSS()}
  {touch_css}
  {self.genHTMLJS()}
  {touch_js}
  <style>
    body.touch-cat {{
      margin: 0; padding: 0;
      min-height: 100dvh;
      display: flex; flex-direction: column;
      background: var(--th-page-bg);
      font-size: 17px;
    }}
    .cat-body {{
      flex: 1; padding: 20px 24px;
      overflow-y: auto;
    }}
    .cat-body h2 {{ margin: 0 0 6px; color: #333; }}
    .cat-body p  {{ margin: 0 0 18px; color: #666; font-size: 0.9em; }}
    .cat-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
      gap: 12px;
      margin-bottom: 24px;
    }}
    /* Square card with background image */
    .cat-card {{
      position: relative;
      border-radius: 10px;
      box-shadow: 0 2px 8px rgba(0,0,0,0.18);
      cursor: pointer;
      user-select: none;
      overflow: hidden;
      aspect-ratio: 1 / 1;
      background-size: cover;
      background-position: center;
      background-color: #d8d0c0;
      transition: transform 0.12s, box-shadow 0.12s;
    }}
    .cat-card:hover  {{ transform: scale(1.03); box-shadow: 0 6px 20px rgba(0,0,0,0.28); }}
    .cat-card:active {{ transform: scale(0.97); }}
    /* Dark gradient overlay at the bottom */
    .cat-card-overlay {{
      position: absolute; inset: 0;
      background: linear-gradient(to bottom, rgba(0,0,0,0.05) 40%, rgba(0,0,0,0.72) 100%);
      display: flex;
      flex-direction: column;
      justify-content: flex-end;
      padding: 10px;
      gap: 4px;
    }}
    .cat-card input[type="checkbox"] {{
      position: absolute; top: 10px; right: 10px;
      width: 24px; height: 24px; cursor: pointer;
      accent-color: var(--th-accent);
    }}
    .cat-card-title {{
      font-weight: bold; font-size: 0.92em;
      color: #fff; text-shadow: 0 1px 3px rgba(0,0,0,0.8);
      line-height: 1.2;
    }}
    .cat-card-count {{
      font-size: 0.75em;
      color: rgba(255,255,255,0.80);
      text-shadow: 0 1px 2px rgba(0,0,0,0.7);
    }}
    .cat-actions {{
      display: flex; gap: 12px; flex-wrap: wrap; align-items: center;
    }}
    .cat-btn {{
      background: var(--th-accent);
      color: #fff; border: none; border-radius: 10px;
      padding: 0 24px; min-height: 48px; font-size: 1em;
      font-family: inherit; font-weight: bold;
      cursor: pointer; transition: background 0.15s;
    }}
    .cat-btn:hover {{ background: var(--th-accent2); }}
    .cat-btn.secondary {{ background: #666; }}
    .cat-btn.secondary:hover {{ background: #444; }}
    #cat-settings-status {{ color: green; font-weight: bold; }}
  </style>
</head>
<body class="touch-cat" onload="initCategorySettingsPage()">

{touch_header}

<div class="cat-body">
  <h2>{_("Category Settings")}</h2>
  <p>{_("Uncheck categories to hide them from the menu, gallery and touch interface.")}</p>
  <div class="cat-grid">
{cards_html}
  </div>
  <div class="cat-actions">
    <button class="cat-btn" onclick="saveCategorySettingsExplicit()">{_("Save")}</button>
    <button class="cat-btn secondary" onclick="resetCategorySettings()">{_("Show all categories")}</button>
    <span id="cat-settings-status" style="display:none">{_("Saved.")}</span>
  </div>
</div>

</body>
</html>
"""
        start_response("200 OK", [("Content-type", "text/html; charset=utf-8")])  # type: ignore[operator]
        return [page.encode("utf-8")]

    # serveGallery → ui_gallery.py (GalleryUIMixin)
