"""Tests for markdown_to_html converter."""

import pytest

from agentic.skills.content.draft_newsletter.markdown_to_html import convert

SCRIPT_MD = """# Video Title

This is the script for the video.

## Introduction

Welcome to this tutorial on Python.

```python
def hello():
    print("Hello, World!")
```

## Main Content

Here we explain the concept.

```javascript
function greet() {
    console.log("Hello!");
}
```

## Conclusion

Thanks for watching!
"""

CITATIONS_MD = """## Citations

- [Python Docs](https://docs.python.org/3/)
- [MDN Web Docs](https://developer.mozilla.org/)
"""

EXPECTED_NEWSLETTER_MD = """# Video Title

This is the script for the video.

## Introduction

Welcome to this tutorial on Python.

```python
def hello():
    print("Hello, World!")
```

## Main Content

Here we explain the concept.

```javascript
function greet() {
    console.log("Hello!");
}
```

## Conclusion

Thanks for watching!

---

## Citations

- [Python Docs](https://docs.python.org/3/)
- [MDN Web Docs](https://developer.mozilla.org/)
"""


def test_convert_creates_kit_compatible_html():
    """Test that convert() produces Kit-compatible HTML with code highlighting."""
    html = convert(SCRIPT_MD)

    # Should be valid HTML structure
    assert html.startswith("<!DOCTYPE html>")
    assert "<html>" in html
    assert "<head>" in html
    assert "<body>" in html
    assert "</html>" in html

    # Should contain code blocks with language classes
    assert 'class="language-python"' in html
    assert 'class="language-javascript"' in html
    assert "<pre" in html
    assert "<code" in html

    # Should contain inline styles for Kit compatibility
    assert "background-color: #f6f8fa" in html
    assert "font-family" in html

    # Should preserve content
    assert "def hello():" in html
    assert "Hello, World!" in html
    assert "function greet()" in html
    assert "Hello!" in html


def test_convert_handles_tables():
    """Test that tables are converted correctly."""
    md_with_table = """# Table Test

| Header 1 | Header 2 |
|----------|----------|
| Cell 1   | Cell 2   |
| Cell 3   | Cell 4   |
"""

    html = convert(md_with_table)

    assert "<table>" in html
    assert "<thead>" in html
    assert "<tbody>" in html
    assert "<th>Header 1</th>" in html
    assert "<td>Cell 1</td>" in html


def test_convert_handles_toc():
    """Test that table of contents is generated."""
    md_with_headers = """# Main Title

## Section 1

Content 1.

## Section 2

Content 2.
"""

    html = convert(md_with_headers)

    # TOC extension should generate anchor links
    assert 'id="main-title"' in html or 'id="section-1"' in html


def test_compose_newsletter_writes_markdown_file(tmp_path):
    """Test that composing newsletter writes newsletter.md to video folder."""
    video_folder = tmp_path / "videos" / "123"
    video_folder.mkdir(parents=True)

    script_path = video_folder / "script.md"
    citations_path = video_folder / "citations.md"
    newsletter_path = video_folder / "newsletter.md"

    script_path.write_text(SCRIPT_MD)
    citations_path.write_text(CITATIONS_MD)

    # Compose newsletter markdown
    newsletter_md = SCRIPT_MD + "\n\n---\n\n" + CITATIONS_MD
    newsletter_path.write_text(newsletter_md)

    # Verify newsletter.md was written
    assert newsletter_path.exists()
    written_content = newsletter_path.read_text()
    assert "Video Title" in written_content
    assert "Citations" in written_content
    assert "Python Docs" in written_content


def test_full_pipeline_script_citations_to_html(tmp_path):
    """Test full pipeline: read script.md and citations.md, compose, convert to HTML."""
    video_folder = tmp_path / "videos" / "456"
    video_folder.mkdir(parents=True)

    script_path = video_folder / "script.md"
    citations_path = video_folder / "citations.md"
    newsletter_path = video_folder / "newsletter.md"

    script_path.write_text(SCRIPT_MD)
    citations_path.write_text(CITATIONS_MD)

    # Step 1: Read and compose
    script_content = script_path.read_text()
    citations_content = citations_path.read_text()
    newsletter_md = script_content + "\n\n---\n\n" + citations_content

    # Step 2: Write newsletter.md
    newsletter_path.write_text(newsletter_md)

    # Step 3: Convert to HTML
    html = convert(newsletter_md)

    # Verify HTML output
    assert 'class="language-python"' in html
    assert 'class="language-javascript"' in html
    assert "Python Docs" in html
    assert "MDN Web Docs" in html
    assert "background-color: #f6f8fa" in html


def test_convert_empty_string():
    """Test converting empty string."""
    html = convert("")
    assert "<!DOCTYPE html>" in html
    assert "<body>" in html
    assert "</body>" in html


def test_convert_inline_code():
    """Test that inline code is preserved."""
    md = "Use `print()` to output text."
    html = convert(md)
    assert "<code>print()</code>" in html


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
