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
sys.path.append(os.path.abspath("../backend/api-gateway/src"))
sys.path.append(os.path.abspath("../backend/feedback-loop"))
sys.path.append(os.path.abspath("../backend/marketplace-publisher/src"))
sys.path.append(os.path.abspath("../backend/monitoring/src"))
sys.path.append(os.path.abspath("../backend/orchestrator"))

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
    "jose",
    "celery",
    "api_gateway",
    "feedback_loop",
    "marketplace_publisher",
    "mockup_generation",
    "monitoring",
    "orchestrator",
    "scoring_engine",
    "signal_ingestion",
    "backend.analytics",
    "backend.shared",
]

source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}

templates_path = ["_templates"]
exclude_patterns: list[str] = ["sphinx/*", "api/*"]

# Treat warnings as errors
nitpicky = True
nitpick_ignore = [
    ("py:class", "datetime.datetime"),
    ("py:class", "ConfigDict"),
    ("py:class", "pathlib.Path"),
]

# -- Options for HTML output -------------------------------------------------

html_theme = "alabaster"
html_static_path = ["_static"]

# Silence warnings for mocked imports
suppress_warnings = [
    "autodoc.mocked_object",
    "toc.duplicate_entry",
    "toc.not_included",
]


# -- Helper functions --------------------------------------------------------


if TYPE_CHECKING:  # pragma: no cover
    from sphinx.application import Sphinx


def _run_linters(app: "Sphinx") -> None:
    """Run docformatter and flake8-docstrings before building docs."""
    docs_dir = os.path.dirname(os.path.abspath(__file__))
    result = subprocess.run(
        ["docformatter", "--check", "--recursive", docs_dir],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(result.stdout)
        raise RuntimeError("docformatter found issues. Run docformatter")
    subprocess.check_call(["flake8", "--select=D", docs_dir])


def _run_apidoc(app: "Sphinx") -> None:
    """
    Generate API docs for all Python modules.

    Parameters
    ----------
    app:
        Instance of :class:`~sphinx.application.Sphinx` representing the current
        build.

    Behavior
    --------
    The function executes :command:`sphinx-apidoc` for every package listed in
    ``("backend", "frontend")``. Setting the ``SKIP_APIDOC`` environment
    variable to ``"1"`` aborts the generation step.
    """
    if os.environ.get("SKIP_APIDOC", "0") == "1":
        return
    output_path = os.path.join(app.srcdir, "api")
    root = os.path.abspath(os.path.join(app.srcdir, ".."))
    for package in ("backend", "frontend"):
        module_path = os.path.join(root, package)
        if not os.path.exists(module_path):
            continue
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
    if os.environ.get("SKIP_OPENAPI", "0") == "1":
        return
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
