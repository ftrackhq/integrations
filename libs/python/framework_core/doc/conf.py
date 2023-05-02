# -*- coding: utf-8 -*-
#
# Configuration file for the Sphinx documentation builder.
#
# This file does only contain a selection of the most common options. For a
# full list see the documentation:
# http://www.sphinx-doc.org/en/master/config

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
from pkg_resources import get_distribution, DistributionNotFound
import sys

# sys.path.insert(0, os.path.abspath('.'))

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'source'))


# -- Project information -----------------------------------------------------

project = u'framework_core'
copyright = u'2020, ftrack'
author = u'ftrack'

# contents of docs/conf.py
try:
    release = get_distribution('ftrack-python-api').version
    # take major/minor/patch
    VERSION = '.'.join(release.split('.')[:3])
except DistributionNotFound:
    # package is not installed
    VERSION = 'Unknown version'

version = VERSION
release = VERSION


# -- General configuration ---------------------------------------------------

# If your documentation needs a minimal Sphinx version, state it here.
#
# needs_sphinx = '1.0'

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.intersphinx',
    'sphinx.ext.todo',
    'sphinx.ext.extlinks',
    'sphinx.ext.viewcode',
    'lowdown',
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# The suffix(es) of source filenames.
# You can specify multiple suffix as a list of string:
#
# source_suffix = ['.rst', '.md']
source_suffix = '.rst'

# The master toctree document.
master_doc = 'index'

modindex_common_prefix = ['framework_core.']

# The language for content autogenerated by Sphinx. Refer to documentation
# for a list of supported languages.
#
# This is also used if you do content translation via gettext catalogs.
# Usually you set "language" from the command line for these cases.
language = 'en'

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = [u'_build', 'Thumbs.db', '.DS_Store', '_template']

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = None


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
# html_theme = 'alabaster'

# Theme options are theme-specific and customize the look and feel of a theme
# further.  For a list of options available for each theme, see the
# documentation.
#
# html_theme_options = {}

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
# html_static_path = ['_static']

# Custom sidebar templates, must be a dictionary that maps document names
# to template names.
#
# The default sidebars (for documents that don't match any pattern) are
# defined by theme itself.  Builtin themes are using these templates by
# default: ``['localtoc.html', 'relations.html', 'sourcelink.html',
# 'searchbox.html']``.
#
# html_sidebars = {}
# on_rtd is whether we are on readthedocs.org
on_rtd = os.environ.get('READTHEDOCS', None) == 'True'

if not on_rtd:  # only import and set the theme if we're building docs locally
    import sphinx_rtd_theme

    html_theme = 'sphinx_rtd_theme'
    html_theme_path = [sphinx_rtd_theme.get_html_theme_path()]

html_static_path = ['_static']
html_style = 'ftrack.css'

# If True, copy source rst files to output for reference.
html_copy_source = True


# -- Options for HTMLHelp output ---------------------------------------------

# Output file base name for HTML help builder.
htmlhelp_basename = 'framework_coredoc'
autodoc_mock_imports = ['jsonschema', 'jsonref', 'python_jsonschema_objects']

# -- Options for LaTeX output ------------------------------------------------

latex_elements = {
    # The paper size ('letterpaper' or 'a4paper').
    #
    # 'papersize': 'letterpaper',
    # The font size ('10pt', '11pt' or '12pt').
    #
    # 'pointsize': '10pt',
    # Additional stuff for the LaTeX preamble.
    #
    # 'preamble': '',
    # Latex figure (float) alignment
    #
    # 'figure_align': 'htbp',
}

# Grouping the document tree into LaTeX files. List of tuples
# (source start file, target name, title,
#  author, documentclass [howto, manual, or own class]).
latex_documents = [
    (
        master_doc,
        'framework_core.tex',
        u'framework_core Documentation',
        u'ftrack',
        'manual',
    ),
]


# -- Options for manual page output ------------------------------------------

# One entry per manual page. List of tuples
# (source start file, name, description, authors, manual section).
man_pages = [
    (
        master_doc,
        'framework_core',
        u'framework_core Documentation',
        [author],
        1,
    )
]


# -- Options for Texinfo output ----------------------------------------------

# Grouping the document tree into Texinfo files. List of tuples
# (source start file, target name, title, author,
#  dir menu entry, description, category)
texinfo_documents = [
    (
        master_doc,
        'framework_core',
        u'framework_core Documentation',
        author,
        'framework_core',
        'One line description of project.',
        'Miscellaneous',
    ),
]


# -- Options for Epub output -------------------------------------------------

# Bibliographic Dublin Core info.
epub_title = project

# The unique identifier of the text. This can be a ISBN number
# or the project homepage.
#
# epub_identifier = ''

# A unique identification for the text.
#
# epub_uid = ''

# A list of files that should not be packed into the epub file.
epub_exclude_files = ['search.html']


# -- Extension configuration -------------------------------------------------

# -- Autodoc ------------------------------------------------------------------

autodoc_default_flags = []  # ['members', 'undoc-members', 'inherited-members']
autodoc_member_order = 'bysource'


def autodoc_skip(app, what, name, obj, skip, options):
    '''Don't skip __init__ method for autodoc.'''
    if name == '__init__':
        return False

    return skip


# -- Options for intersphinx extension ---------------------------------------

# Example configuration for intersphinx: refer to the Python standard library.

intersphinx_mapping = {
    'python': ('http://docs.python.org/', None),
    'ftrack-python-api': (
        'https://ftrack-python-api.readthedocs.io/en/latest/',
        None,
    ),
    'ftrack-connect': (
        'https://ftrack-connect.readthedocs.io/en/latest/',
        None,
    ),
    'ftrack-application-launcher': (
        'https://ftrack-application-launcher.readthedocs.io/en/latest/',
        None,
    ),
    'ftrack-connect-action-launcher-widget': (
        'https://ftrack-connect-action-launcher-widget.readthedocs.io/en/latest/',
        None,
    ),
    'ftrack-connect-publisher-widget': (
        'https://ftrack-connect-publisher-widget.readthedocs.io/en/latest/',
        None,
    ),
    'ftrack-connect-plugin-manager': (
        'https://ftrack-connect-plugin-manager.readthedocs.io/en/latest/',
        None,
    ),
    'ftrack-connect-package': (
        'https://ftrack-connect-package.readthedocs.io/en/latest/',
        None,
    ),
    # TODO: Make intersphinx work with Github hosted docs.
    # 'ftrack-connect-pipeline-definition': (
    #     'https://ftrackhq.github.io/ftrack-connect-pipeline-definition/',
    #    None,
    # ),
    # 'ftrack-connect-pipeline-qt': (
    #    'https://ftrackhq.github.io/ftrack-connect-pipeline-qt/',
    #    None,
    # ),
    # 'ftrack-connect-pipeline-maya': (
    #    'https://ftrackhq.github.io/ftrack-connect-pipeline-maya/',
    #    None,
    # ),
    # 'ftrack-connect-pipeline-nuke': (
    #    'https://ftrackhq.github.io/ftrack-connect-pipeline-nuke/',
    #    None,
    # ),
    # 'ftrack-connect-pipeline-houdini': (
    #    'https://ftrackhq.github.io/ftrack-connect-pipeline-houdini/',
    #    None,
    # ),
    # 'ftrack-connect-pipeline-3dsmax': (
    #     'https://ftrackhq.github.io/ftrack-connect-pipeline-3dsmax/',
    #     None,
    # ),
    #'ftrack-connect-pipeline-unreal': (
    #    'https://ftrackhq.github.io/ftrack-connect-pipeline-unreal/',
    #    None,
    # ),
}

# -- Options for todo extension ----------------------------------------------

# -- Todos ---------------------------------------------------------------------


# If true, `todo` and `todoList` produce output, else they produce nothing.
todo_include_todos = True

# -- Setup --------------------------------------------------------------------


def setup(app):
    app.connect('autodoc-skip-member', autodoc_skip)
