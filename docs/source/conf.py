"""Sphinx configuration for project documentation."""

import os
import sys

sys.path.insert(0, os.path.abspath("../.."))
sys.path.insert(0, os.path.abspath("../../backend/marketplace-publisher/src"))
sys.path.insert(0, os.path.abspath("../../backend/mockup-generation"))

project = "desAInz"
author = "Auto Generated"
extensions = ["sphinx.ext.autodoc"]
autodoc_mock_imports = [
    "asyncpg",
    "selenium",
    "cv2",
    "numpy",
    "torch",
    "transformers",
    "httpx",
    "backend",
    "PIL",
    "monitoring",
]
html_theme = "alabaster"
