# Copyright (C) 2016-2017 Florian Festi
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
from __future__ import annotations


class MenuUIMixin:
    """HTML generation for the classic list/menu page.

    Designed as a mixin for BServer.  All methods use ``self`` attributes
    set by BServer.__init__ (static_url, groups, _cache, …).
    """

    # ── Stubs for attributes provided by BServer ─────────────────────
    static_url: str
    groups: list
    _cache: dict

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

    def genPagePartHeader(self, lang: object) -> str:
        raise NotImplementedError

    def tag_badges_html(self, box: type) -> str:
        raise NotImplementedError

    # ── Menu page ────────────────────────────────────────────────────

    def genPageMenu(self, lang: object):
        """Generate the collapsible category/generator list page."""
        _ = lang.gettext  # type: ignore[attr-defined]
        lang_name = lang.info().get("language", None)  # type: ignore[attr-defined]
        langparam = f"?language={lang_name}" if lang_name else ""

        result = [f"""{self.genHTMLStart(lang)}
<head>
    <title>{_("Boxes.py")}</title>
    {self.genHTMLMeta()}
{self.genHTMLMetaLanguageLink()}
    {self.genHTMLCSS()}
    {self.genHTMLJS()}
</head>
<body onload="initPage()">
<div class="container">
<div style="width: 75%; float: left;">
{self.genPagePartHeader(lang)}
<br>
<div class="menu" style="width: 100%">
<img style="width: 200px;" id="sample-preview" src="{self.static_url}/nothing.png" alt="">
"""]
        for nr, group in enumerate(self.groups):
            result.append(
                f'\n<h3 id="h-{nr}"\n'
                f'    data-id="{nr}"\n'
                f'    data-thumbnail="{self.static_url}/samples/{group.thumbnail}"\n'
                f'    role="button"\n'
                f'    aria-expanded="false"\n'
                f'    class="toggle thumbnail open"\n'
                f'    tabindex="0"\n>\n'
                f"    {_(group.title)}\n</h3>\n"
                f'  <div id="{nr}">\n   <ul>\n'
            )
            for box in group.generators:
                bname = box.__name__
                docs = (" - " + _(box.__doc__)) if box.__doc__ else ""
                badges = self.tag_badges_html(box)
                result.append(
                    f'     <li class="thumbnail" '
                    f'data-thumbnail="{self.static_url}/samples/{bname}-thumb.jpg" '
                    f'id="search_id_{bname}">'
                    f'<a href="{bname}{langparam}">{_(bname)}</a>'
                    f"{badges}{docs}</li>\n"
                )
            result.append("   </ul>\n  </div>\n")
        result.append(f"""
</div>

<div style="width: 5%; float: left;"></div>
<div class="clear"></div>
<hr>
</div>
</div>
</body>
</html>
""")
        return (s.encode("utf-8") for s in result)
