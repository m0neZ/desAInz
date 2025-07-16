project = 'desAInz'
extensions = ['sphinx.ext.autodoc']
exclude_patterns = ['_build']
html_theme = 'alabaster'

import os
import sys
sys.path.insert(0, os.path.abspath('../src'))
