"""Package and distribute the desAInz application."""

from setuptools import Extension, find_packages, setup
import numpy

ext_modules = [
    Extension(
        "scoring_engine._novelty_ext",
        ["backend/scoring-engine/scoring_engine/_novelty_ext.c"],
        include_dirs=[numpy.get_include()],
    )
]

setup(name="desAInz", version="0.1", packages=find_packages(), ext_modules=ext_modules)
