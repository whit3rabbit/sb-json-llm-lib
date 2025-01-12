class ValidationError(Exception):
    """Base validation error."""
    pass

class ParseError(Exception):
    """Error parsing input data."""
    pass

class InvalidSelectorError(ValidationError):
    """Invalid selector error."""
    pass

class InvalidHTMLError(ValidationError):
    """Invalid HTML error."""
    pass