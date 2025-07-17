"""Sphinx configuration for backend modules."""

from __future__ import annotations

import os
import subprocess
import sys
from typing import TYPE_CHECKING

sys.path.insert(0, os.path.abspath("../.."))

project = "desAInz Backend"

extensions = [
    "myst_parser",
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.napoleon",
    "sphinxcontrib.mermaid",
]

autosummary_generate = True
autodoc_mock_imports = [
    "flask",
    "diffusers",
    "redis",
    "torch",
    "numpy",
    "sklearn",
    "sqlalchemy",
    "psycopg2",
    "selenium",
    "apscheduler",
    "scoring_engine",
    "backend.optimization",
    "marketplace_publisher",
    "monitoring",
    "jose",
    "celery",
    "opentelemetry",
]
exclude_patterns = ["_build"]
html_theme = "alabaster"

if TYPE_CHECKING:  # pragma: no cover
    from sphinx.application import Sphinx


def _run_linters(app: "Sphinx") -> None:
    """Run docformatter and flake8-docstrings."""
    docs_dir = os.path.dirname(os.path.abspath(__file__))
    subprocess.check_call(["docformatter", "--in-place", "--recursive", docs_dir])
    subprocess.check_call(["flake8", "--select=D", docs_dir])


def _run_apidoc(app: "Sphinx") -> None:
    """Generate API docs for backend packages."""
    output_path = os.path.join(app.srcdir, "api")
    module_path = os.path.abspath(os.path.join(app.srcdir, "..", "..", "backend"))
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
    """Register hooks for doc build."""
    app.connect("builder-inited", _run_linters)
    app.connect("builder-inited", _run_apidoc)
