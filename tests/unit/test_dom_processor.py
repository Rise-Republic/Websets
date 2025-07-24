import importlib.util
import pathlib
import sys
import types
import pytest

# Load DOMProcessor without importing the app.crawler package to avoid heavy
# dependencies like Playwright and object storage.
MODULE_PATH = pathlib.Path(__file__).resolve().parents[2] / "app/crawler/dom_processor.py"
spec = importlib.util.spec_from_file_location("dom_processor", MODULE_PATH)
dom_processor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dom_processor)
DOMProcessor = dom_processor.DOMProcessor

@pytest.fixture
def processor():
    return DOMProcessor()

HTML_BASIC = """
<!DOCTYPE html>
<html lang='en'>
<head>
<title>Sample Page</title>
<meta name='description' content='A simple page'>
<link rel='canonical' href='https://example.com/page'>
</head>
<body>
<p>Paragraph one.</p>
<p>Contact us at info@example.com or +1 (555) 123-4567</p>
<table id='data'>
<tr><th>A</th><th>B</th></tr>
<tr><td>1</td><td>2</td></tr>
<tr><td>3</td><td>4</td></tr>
</table>
<ul id='list'>
<li>First</li>
<li><a href='#'>Second</a></li>
<li>Third</li>
</ul>
<dl id='defs'>
<dt>Term1</dt><dd>Def1</dd>
<dt>Term2</dt><dd>Def2</dd>
</dl>
<script>var x=1</script>
<style>p{color:red}</style>
</body>
</html>
"""

HTML_INCONSISTENT_TABLE = """
<table>
<tr><th>A</th><th>B</th></tr>
<tr><td>1</td></tr>
</table>
"""

def test_metadata_extraction(processor):
    processor.load_html(HTML_BASIC)
    meta = processor.extract_metadata()
    assert meta["title"] == "Sample Page"
    assert meta["meta_description"] == "A simple page"
    assert meta["canonical_url"] == "https://example.com/page"
    assert meta["language"] == "en"

@pytest.mark.parametrize(
    "method_name", [
        "extract_metadata",
        "find_data_tables",
        "find_structured_lists",
        "extract_text_content",
        "find_contact_info",
        "get_page_statistics",
    ],
)
def test_methods_require_html(processor, method_name):
    method = getattr(processor, method_name)
    with pytest.raises(ValueError):
        method()

def test_find_data_tables(processor):
    html = HTML_BASIC + HTML_INCONSISTENT_TABLE
    processor.load_html(html)
    tables = processor.find_data_tables()
    assert len(tables) == 1, "Only well formed table should be returned"
    table = tables[0]
    assert table["row_count"] == 2
    assert table["column_count"] == 2
    assert table["headers"] == ["A", "B"]

@pytest.mark.parametrize(
    "html,expected",
    [
        ("<ul><li>a</li><li>b</li></ul>", False),
        ("<ul><li>a</li><li>b</li><li>c</li></ul>", True),
    ],
)
def test_analyze_list_edge_cases(processor, html, expected):
    processor.load_html(f"<body>{html}</body>")
    elem = processor.soup.find("ul")
    result = processor._analyze_list(elem)
    assert result["is_structured"] is expected

def test_find_structured_lists(processor):
    processor.load_html(HTML_BASIC)
    lists = processor.find_structured_lists()
    types = {l["type"] for l in lists}
    assert {"ul", "definition_list"} <= types

def test_extract_text_and_contact_info(processor):
    processor.load_html(HTML_BASIC)
    text = processor.extract_text_content()
    assert "var x=1" not in text
    info = processor.find_contact_info()
    assert info["emails"] == ["info@example.com"]
    assert "+1 (555) 123-4567" in info["phones"]

def test_page_statistics(processor):
    processor.load_html(HTML_BASIC)
    stats = processor.get_page_statistics()
    assert stats["paragraph_count"] == 2
    assert stats["table_count"] == 1
    assert stats["list_count"] == 2
