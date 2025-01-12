from enum import Enum
from typing import Dict, Any, Set
from dataclasses import dataclass

from lxml import html, etree
import cssselect

from .exceptions import InvalidSelectorError, InvalidHTMLError
from .utils import (
    normalize_selector,
    extract_selector_parts,
    get_selector_specificity,
    is_valid_html_content
)

class SelectorType(Enum):
    CSS = "css selector"
    XPATH = "xpath"
    TAG = "tag name"
    ID = "id"
    CLASS = "class name"
    EMPTY = "empty"

@dataclass
class SelectorInfo:
    raw_selector: str
    selector_type: SelectorType
    processed_selector: str
    is_valid: bool
    validation_message: str = ""
    specificity: tuple = (0, 0, 0)

class SelectorValidator:
    HTML_TAGS: Set[str] = {
        'div', 'span', 'p', 'a', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
        'article', 'section', 'nav', 'header', 'footer', 'main',
        'aside', 'time', 'figure', 'figcaption', 'img', 'ul', 'ol',
        'li', 'table', 'tr', 'td', 'th', 'thead', 'tbody', 'form',
        'input', 'button', 'textarea'
    }

    def process_selectors(self, selectors: Dict[str, str]) -> Dict[str, Any]:
        """Process and validate a dictionary of selectors."""
        result = {
            "processed_selectors": {},
            "all_valid": True
        }

        for field, selector in selectors.items():
            normalized_selector = normalize_selector(selector)
            
            # Handle empty selectors
            if not normalized_selector:
                result["processed_selectors"][field] = {
                    "type": SelectorType.EMPTY.value,
                    "processed": "",
                    "is_valid": True,
                    "message": "Empty selector",
                    "specificity": (0, 0, 0)
                }
                continue

            try:
                selector_info = self.determine_selector_type(normalized_selector)
                result["processed_selectors"][field] = {
                    "type": selector_info.selector_type.value,
                    "processed": selector_info.processed_selector,
                    "is_valid": selector_info.is_valid,
                    "message": selector_info.validation_message,
                    "specificity": selector_info.specificity
                }
                
                if not selector_info.is_valid:
                    result["all_valid"] = False
                    
            except InvalidSelectorError as e:
                result["processed_selectors"][field] = {
                    "type": "invalid",
                    "processed": normalized_selector,
                    "is_valid": False,
                    "message": str(e),
                    "specificity": (0, 0, 0)
                }
                result["all_valid"] = False

        return result

    def determine_selector_type(self, selector: str) -> SelectorInfo:
        """Determine the type of a selector and validate it."""
        if not selector or not isinstance(selector, str):
            raise InvalidSelectorError("Empty or invalid selector type")

        selector = normalize_selector(selector)
        parts = extract_selector_parts(selector)

        # XPath selector
        if selector.startswith('//') or selector.startswith('(//'):
            try:
                etree.XPath(selector)
                return SelectorInfo(
                    raw_selector=selector,
                    selector_type=SelectorType.XPATH,
                    processed_selector=selector,
                    is_valid=True
                )
            except etree.XPathSyntaxError as e:
                raise InvalidSelectorError(f"Invalid XPath expression: {str(e)}")

        # Simple HTML tag
        if selector.lower() in self.HTML_TAGS and '.' not in selector and '#' not in selector:
            return SelectorInfo(
                raw_selector=selector,
                selector_type=SelectorType.TAG,
                processed_selector=selector.lower(),
                is_valid=True,
                specificity=(0, 0, 1)
            )

        # ID selector
        if parts["id"] and not parts["classes"] and not parts["attributes"] and not parts["tag"]:
            return SelectorInfo(
                raw_selector=selector,
                selector_type=SelectorType.ID,
                processed_selector=f"#{parts['id']}",
                is_valid=True,
                specificity=(1, 0, 0)
            )

        # Class selector
        if parts["classes"] and not parts["id"] and not parts["attributes"] and not parts["tag"]:
            class_name = parts["classes"][0]
            return SelectorInfo(
                raw_selector=selector,
                selector_type=SelectorType.CLASS,
                processed_selector=f".{class_name}",
                is_valid=True,
                specificity=(0, 1, 0)
            )

        # CSS selector
        try:
            cssselect.parse(selector)
            return SelectorInfo(
                raw_selector=selector,
                selector_type=SelectorType.CSS,
                processed_selector=selector,
                is_valid=True,
                specificity=get_selector_specificity(selector)
            )
        except cssselect.SelectorSyntaxError as e:
            raise InvalidSelectorError(f"Invalid CSS selector: {str(e)}")

    def validate_html_content(self, html_content: str, selectors: Dict[str, Dict[str, Any]]) -> Dict[str, bool]:
        """Validate selectors against HTML content."""
        if not is_valid_html_content(html_content):
            raise InvalidHTMLError("Invalid HTML content")

        try:
            tree = html.fromstring(html_content)
            results = {}

            for field, info in selectors.items():
                if not info.get("is_valid", True):
                    results[field] = False
                    continue

                try:
                    selector_type = info.get("type", "")
                    if selector_type == "empty":
                        results[field] = True
                        continue

                    normalized_selector = normalize_selector(info["processed"])
                    
                    if selector_type == "xpath":
                        elements = tree.xpath(normalized_selector)
                    elif selector_type in ("css selector", "class name", "id"):
                        elements = tree.cssselect(normalized_selector)
                    elif selector_type == "tag name":
                        elements = tree.findall(f".//{normalized_selector}")
                    else:
                        elements = []
                        
                    results[field] = len(elements) > 0
                except Exception as e:
                    results[field] = False

            return results
        except etree.ParserError as e:
            raise InvalidHTMLError(f"Error parsing HTML: {str(e)}")