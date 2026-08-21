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

import os
import re


def _convert_table(table_lines: list[str]) -> str:
    """Convert markdown table to HTML."""
    if len(table_lines) < 2:
        return ''

    html_lines = ['<table class="memo-table" style="border-collapse: collapse; width: 100%; margin: 15px 0;">']

    # Parse header row
    header_cells = [cell.strip() for cell in table_lines[0].split('|')[1:-1]]
    html_lines.append('<thead><tr>')
    for cell in header_cells:
        html_lines.append(f'<th style="border: 1px solid #ddd; padding: 10px; text-align: left; background: #f5f5f5;">{cell}</th>')
    html_lines.append('</tr></thead>')

    # Parse data rows (skip separator line)
    html_lines.append('<tbody>')
    for row_line in table_lines[2:]:
        cells = [cell.strip() for cell in row_line.split('|')[1:-1]]
        html_lines.append('<tr>')
        for cell in cells:
            html_lines.append(f'<td style="border: 1px solid #ddd; padding: 10px;">{cell}</td>')
        html_lines.append('</tr>')
    html_lines.append('</tbody>')

    html_lines.append('</table>')
    return '\n'.join(html_lines)


def _markdown_to_html(markdown_text: str) -> tuple[str, str]:
    """Simple markdown to HTML converter for memo content.
    Returns: (html_content, toc_html)
    """
    html_text = markdown_text.strip()
    placeholders = {}
    counter = [0]  # Use list to allow modification in nested function
    toc_items = []  # Extract headers for TOC

    def add_placeholder(html_content: str) -> str:
        key = f"XPHX{counter[0]}XPHX"
        placeholders[key] = html_content
        counter[0] += 1
        return key

    # Headers with IDs
    def header_replacer(m):
        hashes = m.group(1)
        text = m.group(2)
        level = len(hashes)
        header_id = re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')
        toc_items.append((level, text))  # Store for TOC
        return f'<h{level} id="{header_id}">{text}</h{level}>'

    html_text = re.sub(r'^(#{1,3}) (.*?)$', header_replacer, html_text, flags=re.MULTILINE)

    # Inline code (asterisks for special terms like *score*, *cut*, *engrave*) - protect with placeholder
    # Use negative lookbehind/lookahead to avoid matching ** patterns
    def code_replacer(m):
        return add_placeholder(f'<code>*{m.group(1)}*</code>')
    html_text = re.sub(r'(?<!\*)\*([a-z]+)\*(?!\*)', code_replacer, html_text)

    # Bold
    html_text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', html_text)
    html_text = re.sub(r'__(.*?)__', r'<strong>\1</strong>', html_text)

    # Italic
    html_text = re.sub(r'\*(.*?)\*', r'<em>\1</em>', html_text)

    # Restore placeholders AFTER all markdown processing
    for key, value in placeholders.items():
        html_text = html_text.replace(key, value)

    # Process tables first (before lists)
    lines = html_text.split('\n')
    i = 0
    processed_lines = []

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Check if this is a table (line with pipes)
        if '|' in stripped and not stripped.startswith('<'):
            # Collect table lines
            table_lines = [stripped]
            i += 1

            # Check for separator line
            if i < len(lines) and '|' in lines[i].strip():
                sep_line = lines[i].strip()
                if all(c in '|-: ' for c in sep_line):
                    table_lines.append(sep_line)
                    i += 1

                    # Collect remaining table rows
                    while i < len(lines) and '|' in lines[i].strip():
                        table_lines.append(lines[i].strip())
                        i += 1

                    # Convert table to HTML
                    table_html = _convert_table(table_lines)
                    processed_lines.append(table_html)
                    continue

        processed_lines.append(line)
        i += 1

    lines = processed_lines

    # Process lists with nesting support
    result = []
    list_stack = []  # Stack of (type, indent_level)

    for line in lines:
        stripped = line.strip()

        if not stripped:
            result.append('')
            continue

        # Detect indentation level (count leading spaces/tabs)
        indent = len(line) - len(line.lstrip(' \t'))
        indent_level = indent // 2  # Assume 2 spaces per level

        # Check for unordered list item
        if stripped.startswith('- '):
            item_text = stripped[2:].strip()

            # Close lists deeper than current indent
            while list_stack and list_stack[-1][1] > indent_level:
                result.append('  ' * list_stack[-1][1] + f'</{list_stack[-1][0]}>')
                list_stack.pop()

            # Open new list if needed
            if not list_stack or list_stack[-1][0] != 'ul' or list_stack[-1][1] < indent_level:
                result.append('  ' * (indent_level + 1) + '<ul class="memo-list">')
                list_stack.append(('ul', indent_level))

            result.append('  ' * (indent_level + 2) + f'<li>{item_text}</li>')

        # Check for ordered list item
        elif re.match(r'^\d+\. ', stripped):
            item_text = re.sub(r'^\d+\.\s*', '', stripped)

            # Close lists deeper than current indent
            while list_stack and list_stack[-1][1] > indent_level:
                result.append('  ' * list_stack[-1][1] + f'</{list_stack[-1][0]}>')
                list_stack.pop()

            # Open new list if needed
            if not list_stack or list_stack[-1][0] != 'ol' or list_stack[-1][1] < indent_level:
                result.append('  ' * (indent_level + 1) + '<ol class="memo-list">')
                list_stack.append(('ol', indent_level))

            result.append('  ' * (indent_level + 2) + f'<li>{item_text}</li>')

        else:
            # Close any open lists
            while list_stack:
                result.append('  ' * list_stack[-1][1] + f'</{list_stack[-1][0]}>')
                list_stack.pop()

            if not stripped.startswith('<h') and not stripped.startswith('<code>') and not stripped.startswith('<table') and stripped:
                result.append(f'<p>{stripped}</p>')
            elif stripped:
                result.append(stripped)

    # Close remaining open lists
    while list_stack:
        result.append('  ' * list_stack[-1][1] + f'</{list_stack[-1][0]}>')
        list_stack.pop()

    html_output = '\n'.join(result)

    # Generate TOC from headers (only h2 level)
    h2_items = [(level, text) for level, text in toc_items if level == 2]

    if h2_items:
        toc_lines = ['<nav class="memo-toc">', '<ul>']
        for level, text in h2_items:
            header_id = re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')
            toc_lines.append(f'<li><a href="#{header_id}">{text}</a></li>')
        toc_lines.append('</ul>')
        toc_lines.append('</nav>')
        toc_html = '\n'.join(toc_lines)
    else:
        toc_html = ''

    return html_output, toc_html


class MemoUIMixin:
    """Mixin that renders the /memo (laser tips) page."""

    static_url: str
    staticdir: str

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

    def _touch_header_html(self, lang: object, back_url: str = "", back_icon_only: bool = False, center_html: str = "", show_dropdown: bool = True) -> str:
        raise NotImplementedError

    def serveMemo(self, environ: object, start_response: object, lang: object) -> list[bytes]:
        """Render the /memo laser tips page (touch style)."""
        _ = lang.gettext  # type: ignore[attr-defined]
        lang_name = lang.info().get("language", None)  # type: ignore[attr-defined]
        langparam = f"?language={lang_name}" if lang_name else ""

        touch_header = self._touch_header_html(lang, back_url=f"TouchHub{langparam}", back_icon_only=True)

        # Load markdown content based on language
        lang_code = lang_name if lang_name else "en"
        memo_file = os.path.join(self.staticdir, f"memo_{lang_code}.md")

        # Fallback to English if language-specific file doesn't exist
        if not os.path.exists(memo_file):
            memo_file = os.path.join(self.staticdir, "memo_en.md")

        toc_html = ""
        memo_html = ""
        try:
            with open(memo_file, 'r', encoding='utf-8') as f:
                memo_content = f.read()
            memo_html, toc_html = _markdown_to_html(memo_content)
        except FileNotFoundError:
            memo_html = f"<p>{_('Memo content not found')}</p>"

        page = (
            self.genHTMLStart(lang) + "\n"
            "<head>\n"
            f"  <title>{_('Memo')} – {_('Boxes.py')}</title>\n"
            f"  {self.genHTMLMeta()}\n"
            f"  {self.genHTMLCSS()}\n"
            f"  {self.genHTMLTouchCSS()}\n"
            f"  {self.genHTMLJS()}\n"
            f"  {self.genHTMLTouchJS()}\n"
            "<style>\n"
            ".memo-wrapper { display: flex; gap: 20px; flex-direction: row-reverse; }\n"
            ".memo-toc { flex: 0 0 180px; padding: 20px; background: #f9f9f9; border-radius: 8px; position: sticky; top: 100px; height: fit-content; max-height: calc(100vh - 120px); overflow-y: auto; }\n"
            ".memo-toc ul { list-style: none; padding-left: 0; margin: 0; }\n"
            ".memo-toc li { margin: 10px 0; }\n"
            ".memo-toc a { text-decoration: none; color: #0066cc; font-size: 0.9em; }\n"
            ".memo-toc a:hover { text-decoration: underline; }\n"
            ".memo-body { padding: 20px 40px; flex: 1; font-size: 16px; }\n"
            ".memo-body h1 { margin-bottom: 30px; color: #222; scroll-margin-top: 100px; }\n"
            ".memo-body h2 { border-bottom: 2px solid #ddd; padding-bottom: 10px; margin-top: 30px; margin-bottom: 15px; color: #333; scroll-margin-top: 100px; }\n"
            ".memo-body h3 { margin-top: 15px; margin-bottom: 10px; color: #555; font-size: 1.1em; scroll-margin-top: 100px; }\n"
            ".memo-body p { line-height: 1.6; color: #444; margin: 10px 0; }\n"
            ".memo-list { margin-left: 20px; margin-bottom: 15px; }\n"
            ".memo-list li { margin-bottom: 8px; }\n"
            ".memo-body strong { font-weight: 600; }\n"
            ".memo-body code { background: #f5f5f5; padding: 2px 6px; border-radius: 3px; font-family: monospace; color: #d63384; }\n"
            ".memo-body em { font-style: italic; }\n"
            "@media (max-width: 768px) { .memo-wrapper { flex-direction: column; } .memo-toc { flex: 1; position: static; max-height: none; margin-bottom: 20px; } }\n"
            "</style>\n"
            "</head>\n"
            f'<body class="touch-memo">\n'
            f"\n{touch_header}\n\n"
            '<div class="memo-wrapper">\n'
            f"{toc_html}\n"
            '<div class="memo-body">\n'
            f"{memo_html}\n"
            "</div>\n"
            "</div>\n\n"
            "</body>\n</html>\n"
        )
        start_response("200 OK", [("Content-type", "text/html; charset=utf-8")])  # type: ignore[operator]
        return [page.encode("utf-8")]
