"""Markdown to HTML converter for Kit-compatible newsletter output."""

import re

from markdown import Markdown

# Inline CSS styles for Kit-compatible code blocks
CODE_BLOCK_STYLE = (
    "background-color:#1e1e1e;color:#d4d4d4;padding:16px;border-radius:6px;"
    "overflow-x:auto;font-family:'SF Mono',Monaco,Inconsolata,'Fira Mono',"
    "'Droid Sans Mono',monospace;font-size:13px;line-height:1.6;margin:16px 0;"
)

INLINE_CODE_STYLE = (
    "background-color:#f4f4f4;color:#c7254e;padding:2px 6px;border-radius:4px;"
    "font-family:'SF Mono',Monaco,Inconsolata,'Fira Mono','Droid Sans Mono',monospace;"
    "font-size:0.9em;"
)


def _post_process_code_blocks(html: str) -> str:
    """
    Post-process HTML to add inline styles for Kit compatibility.

    Replaces <pre><code class="language-*"> with styled versions.
    Also handles inline <code> tags.
    """

    # Pattern to match <pre><code class="language-*">...</code></pre>
    # Group 1: class attribute value, Group 2: code content
    def replace_pre_code(match: re.Match) -> str:
        lang_class = match.group(1) if match.group(1) else ""
        inner_content = match.group(2)
        # Add inline style to <pre> tag
        styled_pre = f'<pre style="{CODE_BLOCK_STYLE}"><code class="{lang_class}">{inner_content}</code></pre>'
        return styled_pre

    # Match <pre><code class="...">content</code></pre>
    # Group 1 = class attribute, Group 2 = content
    html = re.sub(
        r"<pre><code class=\"([^\"]*)\">(.*?)</code></pre>",
        replace_pre_code,
        html,
        flags=re.DOTALL,
    )

    # Handle inline <code> tags (not inside <pre>)
    def replace_inline_code(match: re.Match) -> str:
        content = match.group(1)
        return f'<code style="{INLINE_CODE_STYLE}">{content}</code>'

    # Match <code>...</code> but not when inside <pre> (already handled)
    # This is a simplified approach - inline code shouldn't contain block elements
    html = re.sub(r"(?<!<pre>)<code>([^<]+)</code>(?!</pre>)", replace_inline_code, html)

    return html


def convert(md: str) -> str:
    """
    Convert Markdown to Kit-compatible HTML.

    Uses Python-Markdown with extensions:
    - codehilite: syntax highlighting with language detection
    - fenced_code: fenced code blocks
    - tables: table support
    - toc: table of contents

    Args:
        md: Markdown string to convert.

    Returns:
        HTML string with inline styles for Kit compatibility.
    """
    md_parser = Markdown(
        extensions=[
            "codehilite",
            "fenced_code",
            "tables",
            "toc",
        ],
        extension_configs={
            "codehilite": {
                "guess_lang": False,  # Don't guess; use explicit language from fence
                "lang_prefix": "language-",  # Class prefix for language
                "css_class": "highlight",  # Base class for codehilite wrapper
                "use_pygments": False,  # Disable Pygments to get language-* classes
            }
        },
        output_format="html",
    )

    html = md_parser.convert(md)
    html = _post_process_code_blocks(html)
    return html
