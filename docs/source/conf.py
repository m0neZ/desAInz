import os
import sys
sys.path.insert(0, os.path.abspath('../..'))
project = 'desAInz'
author = 'desAInz'
extensions = ['myst_parser']
source_suffix = {'.rst': 'restructuredtext', '.md': 'markdown'}
master_doc = 'index'
html_theme = 'alabaster'
suppress_warnings = ['myst.xref_missing', 'misc.highlighting_failure']
