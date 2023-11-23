# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

'''ftrack connect nuke studio documentation build configuration file'''

import os
import re
import sys

import mock
from pkg_resources import DistributionNotFound, get_distribution

# -- General ------------------------------------------------------------------

# Extensions
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.extlinks',
    'sphinx.ext.intersphinx',
    'sphinx.ext.viewcode',
    'lowdown',
]

# The suffix of source filenames.
source_suffix = '.rst'

# The master toctree document.
master_doc = 'index'

# General information about the project.
project = u'ftrack connect nuke studio'
copyright = u'2018, ftrack'

# Version
sources = os.path.realpath(
    os.path.join(os.path.dirname(__file__), '..', 'source')
)
sys.path.append(sources)

try:
    release = get_distribution('nuke-studio').version
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

# A list of prefixes to ignore for module listings
modindex_common_prefix = ['ftrack_nuke_studio.']


# -- HTML output --------------------------------------------------------------

# Determine whether on readthedocs.org
on_rtd = os.environ.get('READTHEDOCS', None) == 'True'

if not on_rtd:
    # Only import and set the theme if building docs locally
    import sphinx_rtd_theme

    html_theme = 'sphinx_rtd_theme'
    html_theme_path = [sphinx_rtd_theme.get_html_theme_path()]

html_static_path = ['_static']
html_style = 'ftrack.css'

# If True, copy source rst files to output for reference.
html_copy_source = True


# -- Autodoc ------------------------------------------------------------------

autodoc_default_flags = ['members']
autodoc_member_order = 'bysource'


def autodoc_skip(app, what, name, obj, skip, options):
    '''Don't skip __init__ method for autodoc.'''
    if name == '__init__':
        return False

    return skip


# Packages / modules to mock so that build does not fail.
for module in [
    'ftrack',
    'ftrack_api',
    'QtExt',
    'ftrack_connect',
    'ui.widget.html_combobox',
    'ftrack_nuke_studio.resource',
    'ftrack_connect.session',
    'lucidity',
    'lucidity.error',
    'ftrack_connect.ui',
    'ftrack_connect.ui.widget',
    'ftrack_connect.ui.widget.html_combobox',
    'ftrack_connect',
    'ui.widget.html_combobox',
    'libpyside2-python2.7.so.2.0',
    'hiero',
    'hiero.core',
    'hiero.core.FnProcessor',
    'hiero.ui',
    'hiero.exporters',
    'exporters.FnShotProcessor',
    'hiero.exporters.FnShotProcessor',
    'hiero.exporters.FnShotProcessorUI',
    'hiero.core.FnExporterBase',
    'foundry',
    'foundry.ui',
    'hiero.ui.FnTaskUIFormLayout',
    'hiero.ui.FnUIProperty',
    'hiero.core.VersionScanner',
    'hiero.exporters.FnTimelineProcessor',
    'hiero.exporters.FnTimelineProcessorUI',
    'hiero.core.events',
    'nuke',
    'hiero.core.util',
    'hiero.exporters.FnNukeShotExporter',
    'hiero.exporters.FnNukeShotExporterUI',
    'hiero.exporters.FnTranscodeExporter',
    'hiero.exporters.FnTranscodeExporterUI',
    'hiero.exporters.FnSubmission',
    'hiero.exporters.FnExternalRender',
    'hiero.exporters.FnAudioExportTask',
    'hiero.exporters.FnAudioExportUI',
    'hiero.exporters.FnEDLExportTask',
    'hiero.exporters.FnEDLExportUI',
]:
    sys.modules[module] = mock.MagicMock()


# -- Intersphinx --------------------------------------------------------------

intersphinx_mapping = {'python': ('http://docs.python.org/', None)}

# -- Setup --------------------------------------------------------------------


def setup(app):
    app.connect('autodoc-skip-member', autodoc_skip)
