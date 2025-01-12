from typing import Dict, Any, Union
from pathlib import Path
import json
import re
from urllib.parse import urlparse
from lxml import etree
import tinycss2

from .exceptions import ValidationError

def is_valid_file_path(path: Union[str, Path]) -> bool:
    """Check if a given path is a valid file path."""
    try:
        return Path(path).exists() and Path(path).is_file()
    except Exception:
        return False

def load_json_data(file_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Load JSON data from a file safely.
    
    Args:
        file_path: Path to the JSON file
        
    Returns:
        Dict containing the JSON data
        
    Raises:
        ValidationError: If file cannot be read or JSON is invalid
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise ValidationError(f"Invalid JSON format: {str(e)}")
    except Exception as e:
        raise ValidationError(f"Error reading file: {str(e)}")

def extract_selector_parts(selector: str) -> Dict[str, str]:
    """
    Extract different parts of a complex selector.
    
    Args:
        selector: The selector string to analyze
        
    Returns:
        Dict containing parts of the selector
    """
    parts = {
        'tag': '',
        'id': '',
        'classes': [],
        'attributes': [],
        'pseudo': []
    }
    
    # Extract ID
    id_match = re.search(r'#([\w-]+)', selector)
    if id_match:
        parts['id'] = id_match.group(1)
    
    # Extract classes
    parts['classes'] = re.findall(r'\.([\w-]+)', selector)
    
    # Extract attributes
    parts['attributes'] = re.findall(r'\[([\w-]+(?:[~|^$*]?=[\w-]+)?)\]', selector)
    
    # Extract pseudo-classes/elements
    parts['pseudo'] = re.findall(r':([\w-]+)(?:\([^)]*\))?', selector)
    
    # Extract tag
    tag_match = re.match(r'^([\w-]+)', selector)
    if tag_match:
        parts['tag'] = tag_match.group(1)
    
    return parts

def is_absolute_url(url: str) -> bool:
    """Check if a URL is absolute."""
    try:
        result = urlparse(url)
        return bool(result.scheme and result.netloc)  # Require both scheme and netloc
    except Exception:
        return False

def merge_selector_results(
    base_results: Dict[str, Any],
    new_results: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Merge two sets of selector results, preserving validation information.
    
    Args:
        base_results: Original results dictionary
        new_results: New results to merge in
        
    Returns:
        Merged results dictionary
    """
    merged = base_results.copy()
    
    # Merge processed selectors
    if "processed_selectors" in new_results:
        if "processed_selectors" not in merged:
            merged["processed_selectors"] = {}
        merged["processed_selectors"].update(new_results["processed_selectors"])
    
    # Merge HTML validation results if present
    if "html_validation" in new_results:
        if "html_validation" not in merged:
            merged["html_validation"] = {}
        merged["html_validation"].update(new_results["html_validation"])
    
    # Update all_valid flag
    if "all_valid" in new_results:
        merged["all_valid"] = merged.get("all_valid", True) and new_results["all_valid"]
    
    return merged

def is_valid_html_content(html_content: str) -> bool:
    """
    Check if content appears to be valid HTML.
    """
    if not html_content or not isinstance(html_content, str):
        return False

    html_content = html_content.strip()
    if not html_content:
        return False

    # First check for bare text without HTML tags
    if not re.search(r'<[^>]+>', html_content):
        return False

    try:
        # Try parsing as XML first (stricter)
        parser = etree.HTMLParser(recover=False)
        etree.fromstring(html_content, parser)
        return True
    except (etree.ParserError, etree.XMLSyntaxError):
        # If it fails, check for common HTML patterns
        has_doctype = bool(re.search(r'<!DOCTYPE\s+html', html_content, re.IGNORECASE))
        has_html_tag = bool(re.search(r'<html[\s>]', html_content, re.IGNORECASE))
        has_body_tag = bool(re.search(r'<body[\s>]', html_content, re.IGNORECASE))
        has_basic_tags = bool(re.search(r'<(?:div|p|h\d|section|article)[\s>]', html_content, re.IGNORECASE))
        
        # Must have at least some HTML structure
        if not (has_doctype or has_html_tag or has_body_tag or has_basic_tags):
            return False
            
        # Check for balanced angle brackets
        open_brackets = len(re.findall(r'<(?![\s/])', html_content))
        close_brackets = len(re.findall(r'</|/>', html_content))
        if open_brackets != close_brackets:
            return False
            
        # Check for malformed tags
        has_malformed = bool(re.search(r'<\w+[^>]*<\w+', html_content))
        if has_malformed:
            return False
            
        return True
    except Exception:
        return False

def get_selector_specificity(selector: str) -> tuple:
    """
    Calculate the specificity of a CSS selector.
    Returns tuple of (id_count, class_count, element_count).
    
    Args:
        selector: CSS selector string
        
    Returns:
        Tuple of (id_count, class_count, element_count)
    """
    parts = extract_selector_parts(selector)
    
    id_count = len(re.findall(r'#[\w-]+', selector))
    class_count = len(parts['classes']) + len(parts['attributes']) + len(parts['pseudo'])
    element_count = 1 if parts['tag'] else 0
    
    return (id_count, class_count, element_count)

def normalize_selector(selector: str) -> str:
    """
    Normalizes a selector that might be XPath or CSS.
    - If it starts with '/' or '//', treat it as XPath (keeps your old logic).
    - Otherwise, parse with tinycss2, preserving descendant combinators and unquoting attribute values.
    """
    if not selector:
        return ""

    # Collapse internal whitespace
    selector = " ".join(selector.split())

    # Check if it's XPath
    if selector.startswith("//") or selector.startswith("/"):
        return _normalize_xpath(selector)
    else:
        return _normalize_css(selector)

def _normalize_xpath(xpath_selector: str) -> str:
    """
    Your existing XPath normalization logic.
    """
    parts = xpath_selector.split("[")
    if len(parts) > 1:
        base = parts[0].strip()
        attrs = "[" + "][".join(p.strip() for p in parts[1:])
        return base + attrs
    return xpath_selector.strip()

def _normalize_css(css_selector: str) -> str:
    """
    Uses tinycss2 to parse CSS. Preserves a single space for descendant combinators,
    removes extra quotes from attribute values (e.g. "[value]" => [value]),
    and removes unwanted spaces around '=', '[', ']', and the combinators > + ~ ,.
    """
    tokens = tinycss2.parse_component_value_list(css_selector)

    result_parts = []
    prev_token = None

    # We'll iterate manually so we can look ahead if needed
    for i, token in enumerate(tokens):
        if token.type == "whitespace":
            # We'll decide below whether to keep a single space
            # (descendant combinator) or skip it entirely.
            continue

        # If we get here, it's not whitespace
        if prev_token and _needs_descendant_space(prev_token, token):
            # Insert a single space for descendant combinator
            result_parts.append(" ")

        if token.type == "hash":
            # e.g. "#myId"
            result_parts.append("#" + token.value)

        elif token.type == "string":
            # tinycss2 unquotes string tokens, so token.value is the inner text
            # Example: "[value]" => token.value == [value], so we just append `[value]`.
            result_parts.append(token.value)

        elif token.type in ("ident", "dimension", "number"):
            # e.g. "div", "content", "10", "100px"
            result_parts.append(token.value)

        else:
            # Delimiters, brackets, colons, equals, plus, tilde, commas, periods, etc.
            # token.serialize() is usually fine here
            result_parts.append(token.serialize())

        prev_token = token

    # Now join the raw parts
    joined = "".join(result_parts)

    # Final cleanup with simple regex:
    # 1) Remove spaces around `[`, `]`.
    joined = re.sub(r"\s*\[\s*", "[", joined)
    joined = re.sub(r"\s*\]\s*", "]", joined)

    # 2) Remove spaces around `=`
    joined = re.sub(r"\s*=\s*", "=", joined)

    # 3) Remove spaces around common combinators (>, +, ~, ,)
    joined = re.sub(r"\s*([>+~,])\s*", r"\1", joined)

    return joined.strip()

def _needs_descendant_space(prev_token, current_token) -> bool:
    """
    Returns True if there's a whitespace token between two tokens that 
    should be separated by a descendant combinator (i.e. `div span`).
    """
    # If both are 'ident', 'hash', 'dimension', or 'number' 
    # (or if the previous was ']' and the current is ident-ish),
    # we want to insert a space.
    # Adjust as needed for your logic:
    if prev_token.type in ("ident", "hash", "dimension", "number", "string", "]") and \
       current_token.type in ("ident", "hash", "dimension", "number", "string", "["):
        return True
    return False