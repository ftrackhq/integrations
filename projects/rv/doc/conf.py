# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

'''rv documentation build configuration file.'''

import os
import re
from pkg_resources import DistributionNotFound, get_distribution

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
project = u'rv'
copyright = u'2021, ftrack'

# Version
try:
    release = get_distribution('rv').version
    # take major/minor/patch
    VERSION = '.'.join(release.split('.')[:2])

except DistributionNotFound:
    # package is not installed
    VERSION = 'Unknown version'

version = VERSION
release = VERSION

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
exclude_patterns = ['_template']

# A list of prefixes to ignore for module listings.
modindex_common_prefix = ['ftrack_rv.']

# -- HTML output --------------------------------------------------------------

# on_rtd is whether currently on readthedocs.org
on_rtd = os.environ.get('READTHEDOCS', None) == 'True'

if not on_rtd:  # only import and set the theme if building docs locally
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
    'ftrack': ('http://rtd.ftrack.com/docs/ftrack/en/latest/', None),
    'ftrack-connect': (
        'http://rtd.ftrack.com/docs/ftrack-connect/en/latest/',
        None,
    ),
}


# -- Todos ---------------------------------------------------------------------

todo_include_todos = True


# -- Setup --------------------------------------------------------------------


def setup(app):
    app.connect('autodoc-skip-member', autodoc_skip)
