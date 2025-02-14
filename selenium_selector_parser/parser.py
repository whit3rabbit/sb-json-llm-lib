from typing import Dict, Optional, Union, Any, Tuple
import json
from pathlib import Path
import logging
from seleniumbase import SB
import tempfile
import os
from bs4 import BeautifulSoup
import re

from pydantic import BaseModel, Field
from .exceptions import ParseError, InvalidHTMLError
from .validators import SelectorValidator
from .utils import (
    load_json_data,
    is_valid_file_path,
    merge_selector_results,
    is_valid_html_content,
    normalize_selector,
    is_absolute_url
)

logger = logging.getLogger(__name__)

class ArticleSelectors(BaseModel):
    url: str = Field(default="")
    title_selector: str = Field(default="")
    author_selector: str = Field(default="")
    date_selector: str = Field(default="")
    content_selector: str = Field(default="")

class SelectorParser:
    """Parser for validating and testing selectors using BeautifulSoup for local HTML and SeleniumBase for URLs."""
    
    def __init__(self, validator: Optional[SelectorValidator] = None):
        self.validator = validator or SelectorValidator()

    def test_selector_with_bs4(
        self,
        soup: BeautifulSoup,
        selector: str,
        selector_type: str
    ) -> Tuple[bool, str, str]:
        """
        Test a selector using BeautifulSoup and return results.
        
        Args:
            soup: BeautifulSoup object
            selector: The selector to test
            selector_type: Type of selector (e.g., 'css selector', 'xpath', 'id', 'class name')
            
        Returns:
            Tuple of (success, status_message, extracted_content)
        """
        if not selector:
            return True, "Empty selector", ""
            
        try:
            elements = []
            
            if selector_type == "xpath":
                # Convert XPath to CSS where possible, or use lxml's xpath
                from lxml import etree
                dom = etree.HTML(str(soup))
                elements = dom.xpath(selector)
                # Convert elements to their text content
                content = ' '.join(e.text.strip() if e.text else '' for e in elements)
                return bool(elements), "Element found" if elements else "Element not found", content
                
            elif selector_type == "css selector":
                elements = soup.select(selector)
            elif selector_type == "id":
                # Remove '#' if present
                id_val = selector.replace('#', '')
                elements = [soup.find(id=id_val)] if soup.find(id=id_val) else []
            elif selector_type == "class name":
                # Remove '.' if present
                class_val = selector.replace('.', '')
                elements = soup.find_all(class_=class_val)
            elif selector_type == "tag name":
                elements = soup.find_all(selector)
                
            if elements:
                # Get text content, handling both single elements and lists
                if isinstance(elements, list):
                    content = ' '.join(elem.get_text(strip=True) for elem in elements if elem)
                else:
                    content = elements.get_text(strip=True)
                return True, "Element found", content
            else:
                return False, "Element not found", ""
                
        except Exception as e:
            error_msg = str(e)
            logger.debug(f"Selector test failed: {error_msg}")
            return False, f"Error finding element: {error_msg}", ""

    def test_selector_in_browser(
        self, 
        sb: SB, 
        selector: str, 
        selector_type: str
    ) -> Tuple[bool, str, str]:
        """
        Test a selector using SeleniumBase and return results.
        
        Args:
            sb: SeleniumBase instance
            selector: The selector to test
            selector_type: Type of selector (e.g., 'css selector', 'xpath')
            
        Returns:
            Tuple of (success, status_message, extracted_content)
        """
        if not selector:
            return True, "Empty selector", ""
            
        try:
            # Add explicit wait for element
            sb.wait_for_ready_state_complete()
            sb.wait_for_element_present(selector, by=selector_type, timeout=10)
            
            # Try to find the element
            element = sb.find_element(selector, by=selector_type)
            if not element:
                return False, "Element not found", ""
                
            # Get text content
            content = sb.get_text(selector, by=selector_type)
            
            # Check visibility
            if sb.is_element_visible(selector, by=selector_type):
                return True, "Element found and visible", content
            else:
                return False, "Element found but not visible", content
                
        except Exception as e:
            error_msg = str(e)
            logger.debug(f"Selector test failed: {error_msg}")
            return False, f"Error finding element: {error_msg}", ""

    def parse_and_validate(
        self,
        json_data: Union[str, Dict[str, str], Path],
        html_content: Optional[Union[str, Path]] = None
    ) -> Dict[str, Any]:
        """
        Parse selectors and validate against HTML content using BeautifulSoup for local HTML
        and SeleniumBase for URLs.
        
        Args:
            json_data: JSON string, file path, or dictionary containing selectors
            html_content: Optional HTML content or file path to validate against
            
        Returns:
            Dictionary containing validation results (with boolean html_validation).
        """
        # Parse JSON data first
        try:
            if isinstance(json_data, (str, Path)) and not isinstance(json_data, dict):
                if is_valid_file_path(json_data):
                    selectors = self.parse_json_file(json_data)
                else:
                    selectors = self.parse_json_string(json_data)
            else:
                selectors = self._process_selectors(json_data)
        except Exception as e:
            raise ParseError(f"Error parsing selectors: {str(e)}")

        # If HTML content is provided, use BeautifulSoup
        if html_content:
            return self._validate_with_bs4(selectors, html_content)
        
        # If no HTML but URL is provided, use SeleniumBase for scraping
        url = selectors.get("processed_selectors", {}).get("url", "")
        if url and is_absolute_url(url):
            return self._validate_with_url(selectors, url)
        
        # If neither HTML nor valid URL provided, return processed selectors
        return selectors

    def _validate_with_bs4(
        self,
        selectors: Dict[str, Any],
        html_content: Union[str, Path]
    ) -> Dict[str, Any]:
        """Validate selectors against provided HTML content using BeautifulSoup."""
        try:
            # Load HTML content
            if is_valid_file_path(html_content):
                with open(html_content, 'r', encoding='utf-8') as f:
                    content = f.read()
            else:
                content = str(html_content)
                if not is_valid_html_content(content):
                    raise InvalidHTMLError("Invalid HTML content")

            # Create BeautifulSoup object
            soup = BeautifulSoup(content, 'html.parser')
            validation_results = {}

            # Test each selector
            for field, info in selectors["processed_selectors"].items():
                # Skip URL field
                if field == "url":
                    validation_results[field] = {
                        "found": True,
                        "status": "URL field",
                        "content": info
                    }
                    continue

                selector_type = info["type"]
                processed_selector = info["processed"]

                # Skip empty selectors
                if not processed_selector:
                    validation_results[field] = {
                        "found": True,
                        "status": "Empty selector",
                        "content": ""
                    }
                    continue

                # Test the selector with BeautifulSoup
                success, status, extracted = self.test_selector_with_bs4(
                    soup, processed_selector, selector_type
                )

                validation_results[field] = {
                    "found": success,
                    "status": status,
                    "content": extracted
                }

            # Convert validation_results to boolean values
            html_validation = {
                field: info["found"] for field, info in validation_results.items()
            }

            # Merge results
            return merge_selector_results(selectors, {"html_validation": html_validation})

        except Exception as e:
            if isinstance(e, InvalidHTMLError):
                raise
            raise InvalidHTMLError(f"Error testing selectors: {str(e)}")

    def _validate_with_url(
        self,
        selectors: Dict[str, Any],
        url: str
    ) -> Dict[str, Any]:
        """Validate selectors by scraping from URL using SeleniumBase."""
        try:
            validation_results = {}
            with SB(headless2=True) as sb:
                sb.open(url)
                sb.wait_for_ready_state_complete()

                # Test each selector
                for field, info in selectors["processed_selectors"].items():
                    if field == "url":
                        validation_results[field] = {
                            "found": True,
                            "status": "URL field",
                            "content": info
                        }
                        continue

                    selector_type = info["type"]
                    processed_selector = info["processed"]

                    if not processed_selector:
                        validation_results[field] = {
                            "found": True,
                            "status": "Empty selector",
                            "content": ""
                        }
                        continue

                    # Convert selector type to SeleniumBase format
                    if selector_type == "css selector":
                        sb_selector_type = "css selector"
                    elif selector_type == "xpath":
                        sb_selector_type = "xpath"
                    elif selector_type == "id":
                        sb_selector_type = "id"
                        processed_selector = processed_selector.lstrip('#')
                    elif selector_type == "class name":
                        sb_selector_type = "class name"
                        processed_selector = processed_selector.lstrip('.')
                    else:
                        sb_selector_type = selector_type

                    # Test the selector in the browser
                    success, status, extracted = self.test_selector_in_browser(
                        sb, processed_selector, sb_selector_type
                    )

                    validation_results[field] = {
                        "found": success,
                        "status": status,
                        "content": extracted
                    }

            # Convert validation_results to boolean values
            html_validation = {
                field: info["found"] for field, info in validation_results.items()
            }

            # Merge results
            return merge_selector_results(selectors, {"html_validation": html_validation})

        except Exception as e:
            raise InvalidHTMLError(f"Error scraping URL: {str(e)}")

    def parse_json_string(self, json_string: str) -> Dict[str, Any]:
        """Parse selectors from a JSON string."""
        try:
            data = json.loads(json_string)
            return self._process_selectors(data)
        except json.JSONDecodeError as e:
            raise ParseError(f"Invalid JSON string: {str(e)}")

    def parse_json_file(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """Parse selectors from a JSON file."""
        if not is_valid_file_path(file_path):
            raise ParseError(f"Invalid or non-existent file: {file_path}")
        try:
            data = load_json_data(file_path)
            return self._process_selectors(data)
        except Exception as e:
            raise ParseError(f"Error loading JSON file: {str(e)}")

    def _process_selectors(self, data: Dict[str, str]) -> Dict[str, Any]:
        """Process and validate selectors."""
        try:
            normalized_data = {
                key: normalize_selector(value)
                for key, value in data.items()
            }
            selectors = ArticleSelectors(**normalized_data)
            return self.validator.process_selectors(selectors.model_dump())
        except Exception as e:
            raise ParseError(f"Invalid selector data format: {str(e)}")