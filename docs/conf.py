"""Sphinx configuration for the desAInz project."""

from __future__ import annotations

import os
import subprocess
import sys
from typing import TYPE_CHECKING

# -- Path setup --------------------------------------------------------------

sys.path.insert(0, os.path.abspath(".."))
sys.path.insert(0, os.path.abspath(os.path.join("..", "backend", "monitoring", "src")))

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

source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}

templates_path = ["_templates"]
exclude_patterns: list[str] = ["scoring_engine/*", "sphinx/*"]

# Treat warnings as errors
nitpicky = True

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
