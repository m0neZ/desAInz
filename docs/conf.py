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
    "sphinx.ext.autosummary",
    "sphinx.ext.napoleon",
    "sphinxcontrib.openapi",
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
]

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


def _run_apidoc(app: "Sphinx") -> None:
    """Generate API docs for all Python modules."""
    output_path = os.path.join(app.srcdir, "api")
    module_path = os.path.abspath(os.path.join(app.srcdir, "..", "backend"))
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


def _generate_openapi(app: "Sphinx") -> None:
    """Generate OpenAPI specifications for all services."""
    root = os.path.abspath(os.path.join(app.srcdir, ".."))
    env = os.environ.copy()
    env["KAFKA_SKIP"] = "1"
    env["SELENIUM_SKIP"] = "1"
    subprocess.check_call(
        [sys.executable, os.path.join(root, "scripts", "generate_openapi.py")],
        env=env,
    )


def setup(app: "Sphinx") -> None:
    """Set up Sphinx hooks."""
    app.connect("builder-inited", _run_linters)
    app.connect("builder-inited", _run_apidoc)
    app.connect("builder-inited", _generate_openapi)
