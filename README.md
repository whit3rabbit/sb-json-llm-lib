# sb-json-llm-lib

This is used for finetuning LLM dataset generation. It may not be useful outside of that.

It takes a JSON of Selenium selectors and either an HTML source or a URL to scrape. It returns types and tests to validate if the selectors can be processed. The library uses BeautifulSoup for efficient local HTML parsing and SeleniumBase for URL scraping.

## Features

- **Selector Parsing & Validation:** Parse selectors from JSON and validate them for CSS, XPath, ID, Class, and Tag.
- **Optimized Processing:** Uses BeautifulSoup for fast local HTML parsing and SeleniumBase for dynamic URL scraping.
- **Content Extraction:** Extract content from HTML elements using validated selectors.
- **URL Scraping Support:** Automatically scrape content from URLs when HTML is not provided.
- **Selector Specificity Calculation:** Compute the specificity of CSS selectors to help with debugging and optimization.
- **Comprehensive Error Handling:** In-depth error feedback for invalid selectors, HTML content, and JSON input.
- **URL Field Support:** An extra `url` key in your JSON input can be used for scraping when no HTML is provided.

## Installation

Install directly from GitHub:

```bash
pip install git+https://github.com/whit3rabbit/sb-json-llm-lib.git
```

## Expected JSON Input Format

The JSON data should represent a dictionary where each key is a name (or identifier) for the selector and each value is the selector string itself. Include a `url` key to provide a URL for scraping when HTML content is not provided.

**Example JSON:**

```json
{
  "title_selector": "h1.article-title",
  "author_selector": "//div[@class='author']",
  "date_selector": "#publish-date",
  "content_selector": "article.content p",
  "url": "https://example.com/article"
}
```

## Performance Optimization

The library uses a hybrid approach for optimal performance:
- **BeautifulSoup** for local HTML content: Much faster and more resource-efficient when working with local HTML
- **SeleniumBase** for URL scraping: Provides full browser capabilities for dynamic web content

Both parsers support the same selector types and formats, ensuring consistent behavior regardless of the source.

## Usage

### Basic Usage

```python
from selenium_selector_parser import SelectorParser

# Initialize parser
parser = SelectorParser()

# Parse and validate local HTML (uses BeautifulSoup for efficiency)
selectors = parser.parse_and_validate(
    json_data='{"title_selector": "h1.title"}',
    html_content='<h1 class="title">Hello</h1>'
)

# Parse and validate by scraping URL (uses SeleniumBase)
selectors = parser.parse_and_validate(
    json_data={
        "title_selector": "h1.title",
        "url": "https://example.com/article"
    }
)
```

### Advanced Usage

```python
# Define multiple selectors
selectors = {
    "title_selector": "h1.article-title",
    "author_selector": "//div[@class='author']",  # XPath selector
    "date_selector": "#publish-date",             # ID selector
    "content_selector": "article.content p",       # CSS selector
    "url": "https://example.com/article"
}

# Option 1: Fast local HTML parsing with BeautifulSoup
html_content = """
<html>
    <h1 class="article-title">Test Article</h1>
    <div class="author">John Doe</div>
    <div id="publish-date">2024-01-11</div>
    <article class="content">
        <p>Article content here</p>
    </article>
</html>
"""
results = parser.parse_and_validate(selectors, html_content)

# Option 2: Dynamic URL scraping with SeleniumBase
results = parser.parse_and_validate(selectors)  # Uses URL from selectors

# Inspect validation results
for field, info in results["html_validation"].items():
    print(f"\n{field}:")
    print(f"  Found: {info['found']}")
    print(f"  Content: {info['content']}")
```

## Supported Selector Types

Both BeautifulSoup and SeleniumBase support these selector types:
- **CSS Selectors:** e.g., `h1.title`, `div > p`
- **XPath Selectors:** e.g., `//div[@class='author']`
- **ID Selectors:** e.g., `#main`
- **Class Selectors:** e.g., `.header`
- **Tag Selectors:** e.g., `div`, `span`

## Return Format Examples

See the [Output Examples](examples/outputs.md) documentation for detailed examples of the return format.

## Development

To set up for development:

```bash
# Clone the repository
git clone https://github.com/whit3rabbit/sb-json-llm-lib.git
cd sb-json-llm-lib

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate

# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/

# Run tests with coverage report
pytest --cov=selenium_selector_parser tests/
```

## Requirements

- Python 3.7+
- [SeleniumBase](https://github.com/seleniumbase/SeleniumBase)
- [BeautifulSoup4](https://www.crummy.com/software/BeautifulSoup/)
- [pydantic](https://pydantic-docs.helpmanual.io/)
- [lxml](https://lxml.de/)
- [cssselect](https://cssselect.readthedocs.io/)
- [tinycss2](https://tinycss2.readthedocs.io/)

## License

This project is licensed under the MIT License – see the [LICENSE](LICENSE) file for details.

## Additional Notes

- **Performance:** The library automatically chooses the most efficient parser:
  - BeautifulSoup for local HTML (faster, less resource-intensive)
  - SeleniumBase for URL scraping (full browser capabilities)
- **URL Scraping:** When HTML content is not provided but a URL is included in the JSON, the library automatically uses SeleniumBase for scraping.
- **Error Handling:** You'll receive detailed error messages for issues with selectors, HTML content, URL scraping, or JSON parsing.
- **Static vs. Dynamic Validation:** The library supports both static content validation (BeautifulSoup) and dynamic content extraction (SeleniumBase).
