"""Sphinx configuration for the desAInz project."""

from __future__ import annotations

import os
import subprocess
import sys
from typing import TYPE_CHECKING

# -- Path setup --------------------------------------------------------------

sys.path.insert(0, os.path.abspath(".."))
sys.path.append(os.path.abspath("../backend/signal-ingestion/src"))
sys.path.append(os.path.abspath("../backend/mockup-generation"))
sys.path.append(os.path.abspath("../backend/scoring-engine"))
sys.path.append(os.path.abspath("../backend"))
sys.path.append(os.path.abspath("../frontend/admin-dashboard"))

# -- Project information -----------------------------------------------------

project = "desAInz"
author = "desAInz Team"
release = "0.1"

# -- General configuration ---------------------------------------------------

extensions = [
    "myst_parser",
    "sphinxcontrib.mermaid",
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
]

autodoc_mock_imports = ["flask", "diffusers", "redis", "torch"]
autodoc_mock_imports += ["numpy", "sklearn", "sqlalchemy"]

source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}

templates_path = ["_templates"]
exclude_patterns: list[str] = []

# Treat warnings as errors
nitpicky = True
nitpick_ignore = [
    ("py:class", "datetime.datetime"),
    ("py:class", "ConfigDict"),
]

# -- Options for HTML output -------------------------------------------------

html_theme = "alabaster"
html_static_path = ["_static"]


# -- Helper functions --------------------------------------------------------


if TYPE_CHECKING:  # pragma: no cover
    from sphinx.application import Sphinx


def _run_linters(app: "Sphinx") -> None:
    """Run docformatter and flake8-docstrings before building docs."""
    docs_dir = os.path.dirname(os.path.abspath(__file__))
    subprocess.check_call(["docformatter", "--in-place", "--recursive", docs_dir])
    subprocess.check_call(["flake8", "--select=D", docs_dir])


def setup(app: "Sphinx") -> None:
    """Set up Sphinx hooks."""
    app.connect("builder-inited", _run_linters)
