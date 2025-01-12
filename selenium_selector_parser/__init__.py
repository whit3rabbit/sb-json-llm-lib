# selenium_selector_parser/__init__.py
from .validators import SelectorValidator, SelectorType, SelectorInfo
from .parser import SelectorParser, ArticleSelectors
from .exceptions import ValidationError, ParseError, InvalidSelectorError, InvalidHTMLError
from .utils import (
    normalize_selector,
    extract_selector_parts,
    get_selector_specificity,
    merge_selector_results,
    is_valid_html_content,
    is_valid_file_path,
    load_json_data
)

__version__ = "0.1.0"

__all__ = [
    # Main classes
    "SelectorValidator",
    "SelectorParser",
    "SelectorType",
    "SelectorInfo",
    "ArticleSelectors",
    
    # Exceptions
    "ValidationError",
    "ParseError",
    "InvalidSelectorError",
    "InvalidHTMLError",
    
    # Utility functions
    "normalize_selector",
    "extract_selector_parts",
    "get_selector_specificity",
    "merge_selector_results",
    "is_valid_html_content",
    "is_valid_file_path",
    "load_json_data"
]