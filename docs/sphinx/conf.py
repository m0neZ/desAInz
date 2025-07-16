"""Sphinx configuration for mockup generation docs."""

project = "mockup_generation"
extensions = ["sphinx.ext.autodoc"]
exclude_patterns = ["_build"]
html_theme = "alabaster"
autodoc_mock_imports = ["PIL"]
