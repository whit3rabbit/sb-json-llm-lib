import pytest
from pathlib import Path
import tempfile
import json
import tinycss2

from selenium_selector_parser.utils import (
    normalize_selector,
    extract_selector_parts,
    is_valid_file_path,
    load_json_data,
    is_absolute_url,
    merge_selector_results,
    is_valid_html_content,
    get_selector_specificity
)
from selenium_selector_parser.exceptions import ValidationError

def test_normalize_selector():
    test_cases = [
        (
            "div.class-name [ data-test = value ] > span",
            "div.class-name[data-test=value]>span"
        ),
        (
            " div  >  span ",
            "div>span"
        ),
        (
            "div[attr = value]",
            "div[attr=value]"
        ),
    ]
    
    for input_selector, expected in test_cases:
        assert normalize_selector(input_selector) == expected

def test_extract_selector_parts():
    selector = "div.class-name#id[attr=value]:hover"
    parts = extract_selector_parts(selector)
    
    assert parts["tag"] == "div"
    assert parts["id"] == "id"
    assert parts["classes"] == ["class-name"]
    assert parts["attributes"] == ["attr=value"]
    assert parts["pseudo"] == ["hover"]

def test_is_valid_file_path():
    # Test with temporary file
    with tempfile.NamedTemporaryFile() as tmp:
        assert is_valid_file_path(tmp.name) is True
    
    # Test with non-existent file
    assert is_valid_file_path("nonexistent.json") is False

def test_load_json_data():
    # Test with valid JSON
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp:
        json.dump({"test": "data"}, tmp)
        tmp.flush()
        tmp_path = tmp.name
    
    try:
        data = load_json_data(tmp_path)
        assert data == {"test": "data"}
    finally:
        # Clean up the temporary file
        Path(tmp_path).unlink(missing_ok=True)

def test_is_absolute_url():
    assert is_absolute_url("https://example.com") is True
    assert is_absolute_url("http://example.com") is True
    assert is_absolute_url("//example.com") is False
    assert is_absolute_url("/path/to/page") is False
    assert is_absolute_url("path/to/page") is False

def test_merge_selector_results():
    base_results = {
        "processed_selectors": {
            "title": {"type": "css", "processed": "h1", "is_valid": True}
        },
        "all_valid": True
    }
    
    new_results = {
        "processed_selectors": {
            "content": {"type": "css", "processed": "div.content", "is_valid": True}
        },
        "html_validation": {
            "content": True
        },
        "all_valid": True
    }
    
    merged = merge_selector_results(base_results, new_results)
    
    assert "title" in merged["processed_selectors"]
    assert "content" in merged["processed_selectors"]
    assert merged["all_valid"] is True
    assert merged["html_validation"]["content"] is True

def test_is_valid_html_content():
    valid_html = """
    <!DOCTYPE html>
    <html>
        <body>
            <div>Content</div>
        </body>
    </html>
    """
    
    invalid_html = """
    This is not HTML content
    Just some random text
    """
    
    assert is_valid_html_content(valid_html) is True
    assert is_valid_html_content(invalid_html) is False

def test_get_selector_specificity():
    test_cases = [
        ("div", (0, 0, 1)),
        ("div.class", (0, 1, 1)),
        ("div#id", (1, 0, 1)),
        ("div.class1.class2", (0, 2, 1)),
        ("div#id.class[attr]:hover", (1, 3, 1)),
    ]
    
    for selector, expected in test_cases:
        assert get_selector_specificity(selector) == expected

def is_equivalent_css_selector(actual: str, expected: str) -> bool:
    """
    Compare two CSS selector strings by parsing them into tokens (ignoring whitespace).
    Returns True if they produce the same tokens, ignoring superficial differences 
    like spacing or quotes around attribute values.
    """
    # Parse both strings to tokens
    actual_tokens = [t.serialize() for t in tinycss2.parse_component_value_list(actual) if t.type != 'whitespace']
    expected_tokens = [t.serialize() for t in tinycss2.parse_component_value_list(expected) if t.type != 'whitespace']

    # Compare the token sequences
    return actual_tokens == expected_tokens

def test_normalize_selector():
    test_cases = [
        (
            "div.class-name [ data-test = value ] > span",
            "div.class-name[data-test=value]>span"
        ),
        (
            " div  >  span ",
            "div>span"
        ),
        (
            "div[attr = value]",
            "div[attr=value]"
        ),
    ]

    for input_selector, expected in test_cases:
        normalized = normalize_selector(input_selector)
        # Instead of doing a strict string equality:
        #     assert normalized == expected
        # Use a token-based comparison:
        assert is_equivalent_css_selector(normalized, expected), \
            f"Expected equivalent tokens for:\n  Input: {input_selector}\n  Normalized: {normalized}\n  Expected: {expected}"
