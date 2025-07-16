"""Sphinx configuration for documentation generation."""

import os
import sys

sys.path.insert(0, os.path.abspath("../.."))

project = "Design Idea Engine"
extensions = ["sphinx.ext.autodoc"]
exclude_patterns: list[str] = []
html_theme = "alabaster"
