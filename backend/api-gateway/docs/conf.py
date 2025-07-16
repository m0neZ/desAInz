"""Sphinx configuration for API Gateway docs."""

import os
import sys

sys.path.insert(0, os.path.abspath("../src"))
project = "API Gateway"
author = "Your Name"
extensions = ["sphinx.ext.autodoc"]
html_theme = "alabaster"
