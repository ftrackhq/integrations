# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

'''ftrack connect documentation build configuration file.'''

import os
import re
import sys
from pkg_resources import get_distribution, DistributionNotFound


sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'source'))
# -- General ------------------------------------------------------------------

# Extensions.
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.extlinks',
    'sphinx.ext.intersphinx',
    'sphinx.ext.todo',
    'sphinx.ext.viewcode',
    'lowdown',
]


# The suffix of source filenames.
source_suffix = '.rst'

# The master toctree document.
master_doc = 'index'

# General information about the project.
project = u'ftrack connect'
copyright = u'2014, ftrack'


try:
    release = get_distribution('ftrack-connect').version
    # take major/minor/patch
    VERSION = '.'.join(release.split('.')[:3])
except DistributionNotFound:
    # package is not installed
    VERSION = 'Unknown version'

version = VERSION
release = VERSION

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
exclude_patterns = ['_template']

# A list of prefixes to ignore for module listings.
modindex_common_prefix = [
    'ftrack_connect',
    'ftrack_connect.',
    'ftrack_connect.ui.',
    'ftrack_connect.ui.widget.',
]

# -- HTML output --------------------------------------------------------------

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


# -- Autodoc ------------------------------------------------------------------

autodoc_default_flags = ['members', 'undoc-members']
autodoc_member_order = 'bysource'


def autodoc_skip(app, what, name, obj, skip, options):
    '''Don't skip __init__ method for autodoc.'''
    if name == '__init__':
        return False

    return skip


# -- Intersphinx --------------------------------------------------------------

intersphinx_mapping = {
    'python': ('http://docs.python.org/', None),
    'ftrack-python-api': (
        'https://ftrack-python-api.readthedocs.io/en/latest/',
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
}


# -- Todos ---------------------------------------------------------------------

todo_include_todos = True

# -- Setup --------------------------------------------------------------------


def setup(app):
    app.connect('autodoc-skip-member', autodoc_skip)
