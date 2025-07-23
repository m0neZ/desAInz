"""
Sphinx configuration for the desAInz project.

Environment variables
---------------------
SKIP_DOC_LINT:
    Skip docstring linting when set to ``"1"``. Defaults to ``"0"``.
SKIP_APIDOC:
    Skip API documentation generation when set to ``"1"``. Defaults to ``"0"``.
SKIP_OPENAPI:
    Skip OpenAPI specification generation when set to ``"1"``. Defaults to
    ``"0"``.
KAFKA_SKIP:
    Set to ``"1"`` while generating OpenAPI specs to disable Kafka connections.
    Defaults to ``"0"``.
SELENIUM_SKIP:
    Set to ``"1"`` while generating OpenAPI specs to disable Selenium usage.
    Defaults to ``"0"``.
"""

from __future__ import annotations

import os
import sys
import subprocess
import asyncio
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
    "sphinx.ext.doctest",
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
    "dagster",
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
    "autodoc.import_object",
    "toc.duplicate_entry",
    "toc.not_included",
]


# -- Helper functions --------------------------------------------------------


if TYPE_CHECKING:  # pragma: no cover
    from sphinx.application import Sphinx


from typing import Any


async def _run(cmd: list[str], **kwargs: Any) -> None:
    """Run an external command asynchronously."""
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
        **kwargs,
    )
    stdout, _ = await process.communicate()
    if process.returncode != 0:
        if stdout:
            print(stdout.decode())
        raise RuntimeError(f"Command {' '.join(cmd)} failed")


async def _linters_task() -> None:
    """Run docformatter and flake8-docstrings before building docs."""
    if os.environ.get("SKIP_DOC_LINT", "0") == "1":
        return
    docs_dir = os.path.dirname(os.path.abspath(__file__))
    proc = await asyncio.create_subprocess_exec(
        "docformatter",
        "--check",
        "--recursive",
        docs_dir,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    stdout, _ = await proc.communicate()
    if proc.returncode != 0:
        if stdout:
            print(stdout.decode())
        raise RuntimeError("docformatter found issues. Run docformatter")
    await _run(["flake8", "--select=D", docs_dir])


async def _apidoc_task(app: "Sphinx") -> None:
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
        await _run(
            [
                "sphinx-apidoc",
                "--force",
                "--module-first",
                "--output-dir",
                output_path,
                module_path,
            ]
        )


async def _openapi_task(app: "Sphinx") -> None:
    """Generate OpenAPI specifications for all services."""
    if os.environ.get("SKIP_OPENAPI", "0") == "1":
        return
    root = os.path.abspath(os.path.join(app.srcdir, ".."))
    env = os.environ.copy()
    env["KAFKA_SKIP"] = "1"
    env["SELENIUM_SKIP"] = "1"
    await _run(
        [sys.executable, os.path.join(root, "scripts", "generate_openapi.py")],
        env=env,
    )


def setup(app: "Sphinx") -> None:
    """Set up Sphinx hooks."""

    def _pre_build(app: "Sphinx") -> None:
        async def _tasks() -> None:
            await asyncio.gather(
                _linters_task(),
                _apidoc_task(app),
                _openapi_task(app),
            )

        asyncio.run(_tasks())

    app.connect("builder-inited", _pre_build)
