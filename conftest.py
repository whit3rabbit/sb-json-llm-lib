import pytest
from selenium_selector_parser import SelectorParser

def pytest_addoption(parser):
    parser.addoption(
        "--run-browser",
        action="store_true",
        default=False,
        help="run browser-based tests"
    )

def pytest_configure(config):
    config.addinivalue_line(
        "markers", "browser: mark test as requiring browser"
    )

def pytest_collection_modifyitems(config, items):
    if not config.getoption("--run-browser"):
        skip_browser = pytest.mark.skip(reason="need --run-browser option to run")
        for item in items:
            if "browser" in item.keywords:
                item.add_marker(skip_browser)

@pytest.fixture
def parser():
    """Return an instance of the SelectorParser class."""
    return SelectorParser()