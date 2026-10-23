"""Markdown to HTML converter with code highlighting for Kit."""

import markdown


def convert(md: str) -> str:
    """Convert Markdown to Kit-compatible HTML with code highlighting.

    Args:
        md: Markdown string to convert.

    Returns:
        HTML string with inline CSS for code blocks, compatible with Kit.
    """
    extensions = [
        "pymdownx.highlight",
        "fenced_code",
        "tables",
        "toc",
    ]

    extension_configs = {
        "pymdownx.highlight": {
            "use_pygments": True,
            "noclasses": True,  # Use inline styles
            "css_class": "highlight",
            "pygments_style": "default",
        },
        "toc": {
            "permalink": True,
        },
    }

    md_converter = markdown.Markdown(
        extensions=extensions,
        extension_configs=extension_configs,
        output_format="html",
    )

    html = md_converter.convert(md)

    # Post-process to ensure language classes are on code tags
    html = _post_process_code_blocks(html)

    # Wrap in a minimal HTML structure with inline CSS for Kit compatibility
    kit_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        /* Kit-compatible inline styles for code blocks */
        pre {{
            background-color: #f6f8fa;
            border-radius: 6px;
            padding: 16px;
            overflow: auto;
            font-family: "SF Mono", "Fira Code", "Fira Mono", Menlo, Consolas, monospace;
            font-size: 14px;
            line-height: 1.6;
        }}
        code {{
            font-family: "SF Mono", "Fira Code", "Fira Mono", Menlo, Consolas, monospace;
            font-size: 14px;
        }}
        pre code {{
            background: none;
            padding: 0;
            font-size: inherit;
        }}
        .highlight {{
            background-color: #f6f8fa;
        }}
        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 16px 0;
        }}
        th, td {{
            border: 1px solid #d0d7de;
            padding: 8px 12px;
            text-align: left;
        }}
        th {{
            background-color: #f6f8fa;
            font-weight: 600;
        }}
        tr:nth-child(2n) {{
            background-color: #f6f8fa;
        }}
    </style>
</head>
<body>
{html}
</body>
</html>"""

    return kit_html


def _post_process_code_blocks(html: str) -> str:
    """Post-process HTML to ensure language classes are on code tags.

    The pymdownx.highlight with noclasses=True produces:
    <div class="highlight" style="..."><pre style="..."><code>...</code></pre></div>

    We want:
    <pre style="..."><code class="language-*">...</code></pre>
    """
    import re

    # Pattern to match highlight div with pre and code inside
    pattern = r'<div class="highlight" style="([^"]*)"><pre style="([^"]*)"><code>(.*?)</code></pre></div>'

    def replace_code_block(match):
        div_style = match.group(1)
        pre_style = match.group(2)
        code_content = match.group(3)

        # Extract language from the first highlighted token if possible
        # The first span typically indicates the language (e.g., keyword, function)
        # We'll try to detect from common patterns in the content
        language = _detect_language(code_content)

        # Combine styles: div style + pre style
        combined_style = f"{div_style}; {pre_style}".replace("; ;", ";").strip("; ")

        return f'<pre style="{combined_style}"><code class="language-{language}">{code_content}</code></pre>'

    html = re.sub(pattern, replace_code_block, html, flags=re.DOTALL)

    return html


def _detect_language(code_content: str) -> str:
    """Detect programming language from highlighted code content.

    Looks at the first few highlighted tokens to guess the language.
    """
    # Common patterns for different languages
    if "function" in code_content and ("{" in code_content or "=>" in code_content):
        return "javascript"
    if "def " in code_content and ":" in code_content:
        return "python"
    if "public class" in code_content or "public static void" in code_content:
        return "java"
    if "#include" in code_content or "int main" in code_content:
        return "cpp"
    if "fn " in code_content and "{" in code_content:
        return "rust"
    if "func " in code_content and "{" in code_content:
        return "go"
    if "SELECT" in code_content.upper() and "FROM" in code_content.upper():
        return "sql"
    if "<html" in code_content.lower() or "<div" in code_content.lower():
        return "html"
    if "{" in code_content and "}" in code_content and ":" in code_content and ";" in code_content:
        return "css"

    # Default to python
    return "python"
