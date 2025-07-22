"""Sphinx configuration for project documentation."""

from __future__ import annotations

import os
import subprocess
import sys
from typing import TYPE_CHECKING

sys.path.insert(0, os.path.abspath("../.."))

project = "desAInz"
author = "Auto Generated"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.napoleon",
    "myst_parser",
]

autosummary_generate = True
html_theme = "alabaster"

if TYPE_CHECKING:  # pragma: no cover
    from sphinx.application import Sphinx


def _run_linters(app: "Sphinx") -> None:
    """Run docformatter and flake8-docstrings."""
    docs_dir = os.path.dirname(os.path.abspath(__file__))
    subprocess.check_call(["docformatter", "--in-place", "--recursive", docs_dir])
    subprocess.check_call(["flake8", "--select=D", docs_dir])


def _run_apidoc(app: "Sphinx") -> None:
    """Generate API docs for all subpackages."""
    output_path = os.path.join(app.srcdir, "api")
    root = os.path.abspath(os.path.join(app.srcdir, "..", ".."))
    for package in ("backend", "scripts"):
        module_path = os.path.join(root, package)
        if os.path.exists(module_path):
            subprocess.check_call(
                [
                    "sphinx-apidoc",
                    "--force",
                    "--module-first",
                    "--output-dir",
                    output_path,
                    module_path,
                ]
            )


def setup(app: "Sphinx") -> None:
    """Register Sphinx hooks."""
    app.connect("builder-inited", _run_linters)
    app.connect("builder-inited", _run_apidoc)
