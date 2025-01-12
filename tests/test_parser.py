import pytest
from selenium_selector_parser import SelectorParser, ParseError, InvalidHTMLError
import json

def test_parse_json_string_valid():
    parser = SelectorParser()
    json_string = '''
    {
        "title_selector": "h1.title",
        "author_selector": "//div[@class='author']",
        "date_selector": "#date",
        "content_selector": "div.content"
    }
    '''
    result = parser.parse_json_string(json_string)
    assert result["all_valid"] is True
    assert len(result["processed_selectors"]) == 4

def test_parse_json_string_invalid():
    parser = SelectorParser()
    with pytest.raises(ParseError):
        parser.parse_json_string("invalid json")

def test_parse_and_validate_with_html():
    parser = SelectorParser()
    json_string = '''
    {
        "title_selector": "h1.title",
        "content_selector": "div.content"
    }
    '''
    html_content = '''
    <html>
        <h1 class="title">Test Title</h1>
        <div class="content">Test Content</div>
    </html>
    '''
    # Parse JSON first
    data = json.loads(json_string)
    result = parser.parse_and_validate(data, html_content)
    assert "html_validation" in result
    assert result["html_validation"]["title_selector"] is True
    assert result["html_validation"]["content_selector"] is True

def test_parse_and_validate_with_invalid_html():
    parser = SelectorParser()
    json_string = '{"title_selector": "h1.title"}'
    html_content = '<invalid<html>'
    data = json.loads(json_string)
    
    with pytest.raises(InvalidHTMLError):
        parser.parse_and_validate(data, html_content)

def test_parse_and_validate_with_invalid_xpath():
    parser = SelectorParser()
    json_string = '{"title_selector": "//[invalid"}'
    result = parser.parse_json_string(json_string)
    assert result["processed_selectors"]["title_selector"]["is_valid"] is False

def test_parse_and_validate_with_complex_html():
    parser = SelectorParser()
    
    json_string = ('{'
        '"title_selector": "//h1[@class=\'title\']",'
        '"author_selector": ".author > span",'
        '"date_selector": "#publication-date",'
        '"content_selector": "article.content p"'
    '}')
    
    html_content = (
        '<html><body>'
        '<h1 class="title">Complex Test</h1>'
        '<div class="author"><span>John Doe</span></div>'
        '<time id="publication-date">2024-01-11</time>'
        '<article class="content">'
        '<p>First paragraph</p>'
        '<p>Second paragraph</p>'
        '</article>'
        '</body></html>'
    )
    
    print("\n=== Test Input ===")
    print(f"JSON string: {json_string}")
    print(f"HTML content: {html_content}")

    data = json.loads(json_string)
    
    # Add debug to SelectorParser.test_selector_in_browser method
    original_test_selector = parser.test_selector_in_browser
    
    def debug_test_selector(sb, selector, selector_type):
        print(f"\n=== Testing Selector ===")
        print(f"Selector: {selector}")
        print(f"Selector type: {selector_type}")
        try:
            print(f"Page source: {sb.get_page_source()[:500]}...")  # First 500 chars
            result = original_test_selector(sb, selector, selector_type)
            print(f"Test result: {result}")
            return result
        except Exception as e:
            print(f"Error testing selector: {str(e)}")
            raise
    
    parser.test_selector_in_browser = debug_test_selector
    
    result = parser.parse_and_validate(data, html_content)
    
    print("\n=== Validation Result ===")
    print(f"Full result: {json.dumps(result, indent=2)}")

    # Restore original method
    parser.test_selector_in_browser = original_test_selector

    assert "html_validation" in result
    assert result["html_validation"]["title_selector"] is True, \
        f"Title selector validation failed. Raw result: {result['html_validation']['title_selector']}"
    assert result["html_validation"]["author_selector"] is True
    assert result["html_validation"]["date_selector"] is True
    assert result["html_validation"]["content_selector"] is True

def test_selenium_content_extraction(parser):
    json_string = '''
    {
        "title_selector": "h1.title",
        "content_selector": "div.content"
    }
    '''
    html_content = '''
    <html>
        <h1 class="title">Test Title</h1>
        <div class="content">Test Content</div>
    </html>
    '''
    # Skip this test if we're not running browser tests
    pytest.skip("Skipping browser-based test")

