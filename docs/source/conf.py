"""Sphinx configuration for the main documentation."""

import os
import sys

sys.path.insert(0, os.path.abspath("../.."))

project = "desAInz"
author = "Auto Generated"
extensions = ["sphinx.ext.autodoc"]
html_theme = "alabaster"
autodoc_mock_imports = ["redis", "PIL"]
