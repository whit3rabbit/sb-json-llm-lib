import pytest
from selenium_selector_parser import (
    SelectorValidator,
    InvalidHTMLError,
    SelectorType,
    InvalidSelectorError
)

def test_validate_css_selector():
    validator = SelectorValidator()
    selector_info = validator.determine_selector_type("div.class-name")
    assert selector_info.is_valid is True
    assert selector_info.selector_type == SelectorType.CSS

def test_validate_xpath_selector():
    validator = SelectorValidator()
    selector_info = validator.determine_selector_type("//div[@class='author']")
    assert selector_info.is_valid is True
    assert selector_info.selector_type == SelectorType.XPATH

def test_validate_html_tag():
    validator = SelectorValidator()
    selector_info = validator.determine_selector_type("div")
    assert selector_info.is_valid is True
    assert selector_info.selector_type == SelectorType.TAG
    assert selector_info.specificity == (0, 0, 1)

def test_validate_invalid_selector():
    validator = SelectorValidator()
    with pytest.raises(InvalidSelectorError):
        validator.determine_selector_type("[invalid[selector]")

def test_process_multiple_selectors():
    validator = SelectorValidator()
    selectors = {
        "title": "h1.title",
        "author": "//div[@class='author']",
        "content": "div#content",
    }
    result = validator.process_selectors(selectors)
    assert result["all_valid"] is True
    assert len(result["processed_selectors"]) == 3
    assert result["processed_selectors"]["title"]["type"] == "css selector"
    assert result["processed_selectors"]["author"]["type"] == "xpath"
    assert result["processed_selectors"]["content"]["type"] == "css selector"

def test_selector_specificity():
    validator = SelectorValidator()
    selector_info = validator.determine_selector_type("div#main.content[data-test]")
    assert selector_info.is_valid is True
    assert selector_info.selector_type == SelectorType.CSS
    assert selector_info.specificity == (1, 2, 1)  # 1 ID, 2 (class + attribute), 1 element

def test_validate_html_content():
    validator = SelectorValidator()
    html_content = """
    <html>
        <h1 class="title">Test Title</h1>
        <div class="author">John Doe</div>
        <div id="content">Test content</div>
    </html>
    """
    selectors = {
        "title": {
            "type": "css selector",
            "processed": "h1.title",
            "is_valid": True
        },
        "author": {
            "type": "css selector",
            "processed": ".author",
            "is_valid": True
        }
    }
    results = validator.validate_html_content(html_content, selectors)
    assert results["title"] is True
    assert results["author"] is True

def test_invalid_html_content():
    validator = SelectorValidator()
    html_content = "<invalid<html>"
    selectors = {
        "title": {
            "type": "css selector",
            "processed": "h1",
            "is_valid": True
        }
    }
    with pytest.raises(InvalidHTMLError):
        validator.validate_html_content(html_content, selectors)

def test_empty_selector():
    validator = SelectorValidator()
    with pytest.raises(InvalidSelectorError, match="Empty or invalid selector type"):
        validator.determine_selector_type("")

def test_normalize_selector_processing():
    validator = SelectorValidator()
    selector_info = validator.determine_selector_type(" div.class-name [ data-test = value ] ")
    assert selector_info.is_valid is True
    assert selector_info.processed_selector == "div.class-name[data-test=value]"