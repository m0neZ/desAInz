SPHINXBUILD ?= sphinx-build
SOURCEDIR = .
BUILDDIR = _build

.PHONY: html doctest
html:
	$(SPHINXBUILD) -b html -W -n $(SOURCEDIR) $(BUILDDIR)/html

doctest:
	$(SPHINXBUILD) -b doctest -n $(SOURCEDIR) $(BUILDDIR)/doctest
