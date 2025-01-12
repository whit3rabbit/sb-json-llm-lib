from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="selenium-selector-parser",
    version="0.1.0",
    author="whit3rabbit",
    author_email="whiterabbit@protonmail.com",
    description="A library for parsing and validating Selenium selectors from LLM output",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/whit3rabbit/sb-json-llm-lib",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "cssselect>=1.2.0",
        "lxml>=4.9.0",
        "pydantic>=2.0.0",
        "seleniumbase>=4.33.14",
        "tinycss2>=1.4.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=22.0.0",
            "isort>=5.0.0",
            "mypy>=0.990",
        ],
    }
)