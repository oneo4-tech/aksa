"""Tests for the markdown_to_html converter."""

import importlib.util
import sys
from pathlib import Path

# Load the markdown_to_html module from the hyphenated directory
_md_path = (
    Path(__file__).resolve().parents[1]
    / "agentic"
    / "skills"
    / "content"
    / "draft-newsletter"
    / "scripts"
    / "markdown_to_html.py"
)
_spec = importlib.util.spec_from_file_location("draft_newsletter_markdown_to_html", _md_path)
_md_module = importlib.util.module_from_spec(_spec)
sys.modules["draft_newsletter_markdown_to_html"] = _md_module
_spec.loader.exec_module(_md_module)

convert = _md_module.convert


class TestMarkdownToHtml:
    """Tests for the convert function."""

    def test_basic_conversion(self):
        """Test basic markdown to HTML conversion."""
        md = "# Hello\n\nWorld"
        html = convert(md)
        assert "<h1" in html
        assert "Hello</h1>" in html
        assert "<p>World</p>" in html

    def test_inline_code(self):
        """Test inline code conversion with Kit styles."""
        md = "Use `print()` function."
        html = convert(md)
        assert 'style="' in html
        assert "INLINE_CODE_STYLE" not in html  # Style should be inlined
        assert "background-color:#f4f4f4" in html
        assert "color:#c7254e" in html
        assert "<code" in html
        assert "print()" in html

    def test_fenced_code_block_python(self):
        """Test fenced code block with Python language."""
        md = '```python\ndef hello():\n    print("Hello")\n```'
        html = convert(md)
        assert "<pre" in html
        assert 'class="language-python"' in html
        assert 'style="' in html
        assert "background-color:#1e1e1e" in html
        assert "def hello():" in html
        assert "Hello" in html  # Content preserved (quotes HTML-escaped)

    def test_fenced_code_block_javascript(self):
        """Test fenced code block with JavaScript language."""
        md = '```javascript\nconsole.log("test");\n```'
        html = convert(md)
        assert 'class="language-javascript"' in html
        assert "console.log" in html

    def test_plain_code_block(self):
        """Test plain code block without language."""
        md = "```\nplain text\n```"
        html = convert(md)
        assert "<pre" in html
        assert "plain text" in html

    def test_table_conversion(self):
        """Test table conversion."""
        md = "| A | B |\n|---|---|\n| 1 | 2 |"
        html = convert(md)
        assert "<table>" in html
        assert "<th>A</th>" in html
        assert "<th>B</th>" in html
        assert "<td>1</td>" in html
        assert "<td>2</td>" in html

    def test_toc_extension(self):
        """Test that TOC extension works."""
        md = "# Header 1\n\n## Header 2\n\n### Header 3"
        html = convert(md)
        assert "<h1" in html
        assert "<h2" in html
        assert "<h3" in html

    def test_script_fixture(self):
        """Test conversion of script.md fixture."""
        fixture_path = Path(__file__).parent / "fixtures" / "script.md"
        md = fixture_path.read_text()
        html = convert(md)

        # Check for key elements
        assert "<h1" in html
        assert "Newsletter Script Example" in html
        assert 'class="language-python"' in html
        assert 'class="language-javascript"' in html
        assert "def hello_world():" in html
        assert "function greet" in html
        assert "<table>" in html
        assert "Column 1" in html

        # Check Kit-compatible styles
        assert "background-color:#1e1e1e" in html
        assert "background-color:#f4f4f4" in html

    def test_citations_fixture(self):
        """Test conversion of citations.md fixture."""
        fixture_path = Path(__file__).parent / "fixtures" / "citations.md"
        md = fixture_path.read_text()
        html = convert(md)

        # Check for key elements
        assert "<h1" in html
        assert "Citations Example" in html
        assert 'class="language-python"' in html
        assert "def fibonacci" in html
        assert "<table>" in html
        assert "Source" in html

        # Check Kit-compatible styles
        assert "background-color:#1e1e1e" in html

    def test_newsletter_md_written(self, tmp_path):
        """Test that newsletter.md can be written with converted HTML."""
        fixture_path = Path(__file__).parent / "fixtures" / "script.md"
        md = fixture_path.read_text()
        html = convert(md)

        output_path = tmp_path / "newsletter.md"
        output_path.write_text(html)

        assert output_path.exists()
        content = output_path.read_text()
        assert 'class="language-python"' in content
        assert 'style="' in content
        assert "background-color:#1e1e1e" in content

    def test_empty_input(self):
        """Test empty input handling."""
        html = convert("")
        assert html == ""

    def test_only_whitespace(self):
        """Test whitespace-only input."""
        html = convert("   \n\n  ")
        # Should produce minimal output
        assert isinstance(html, str)

    def test_special_characters_in_code(self):
        """Test code blocks with special HTML characters."""
        md = '```python\nif x < 5 and y > 10:\n    print("x < y")\n```'
        html = convert(md)
        # HTML escaping is expected
        assert "<" in html
        assert ">" in html
        assert "x &lt; 5" in html

    def test_nested_formatting_in_code(self):
        """Test that code blocks preserve formatting."""
        md = "```python\n# Comment with *asterisks* and _underscores_\n```"
        html = convert(md)
        assert "*asterisks*" in html
        assert "_underscores_" in html

    def test_multiple_code_blocks(self):
        """Test multiple code blocks in one document."""
        md = "```python\nprint(1)\n```\n\n```javascript\nconsole.log(2);\n```"
        html = convert(md)
        assert html.count('class="language-python"') == 1
        assert html.count('class="language-javascript"') == 1
        assert "print(1)" in html
        assert "console.log(2)" in html
