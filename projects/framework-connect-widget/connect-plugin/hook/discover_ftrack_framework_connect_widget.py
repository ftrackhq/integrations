# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack
import os
import sys
import logging
import functools

import ftrack_api

from ftrack_utils.version import get_connect_plugin_version

NAME = 'framework-connect-widget'

logger = logging.getLogger(__name__)

cwd = os.path.dirname(__file__)
connect_plugin_path = os.path.abspath(os.path.join(cwd, '..'))

# Read version number from __version__.py
__version__ = get_connect_plugin_version(connect_plugin_path)

python_dependencies = os.path.abspath(
    os.path.join(connect_plugin_path, 'dependencies')
)
sys.path.append(python_dependencies)

from ftrack_utils.extensions.environment import (
    get_extensions_path_from_environment,
)


def on_discover_integration(session, event):
    selection = event['data'].get('context', {}).get('selection', [])

    if selection:
        task = session.get('Context', selection[0]['entityId'])
        os.environ['FTRACK_CONTEXTID'] = task['id']

    extensions_path = get_extensions_path_from_environment()
    if not extensions_path:
        extensions_path = get_default_extensions_path() or []
        if isinstance(extensions_path, list):
            os.environ[
                'FTRACK_FRAMEWORK_EXTENSIONS_PATH'
            ] = os.path.pathsep.join(extensions_path)
        else:
            os.environ['FTRACK_FRAMEWORK_EXTENSIONS_PATH'] = extensions_path
        logger.debug(
            f"os.environ['FTRACK_FRAMEWORK_EXTENSIONS_PATH'] --> {os.environ['FTRACK_FRAMEWORK_EXTENSIONS_PATH']}"
        )

    import ftrack_framework_connect_widget

    data = {
        'integration': {
            'name': NAME,
            'version': __version__,
        }
    }
    return data


def get_default_extensions_path():
    """Get the absolute path to the extensions directory based on the location of this script."""
    # __file__ refers to the path of the current script (my-hook.py in this case)
    # Get the directory of the current script
    current_script_path = os.path.abspath(__file__)

    # Get the 'hook' directory by finding the directory of the current script
    hook_dir = os.path.dirname(current_script_path)
    # Get the 'plugin' directory by going up one level from the 'hook' directory
    plugin_dir = os.path.dirname(hook_dir)

    # Construct the path to the 'extensions' directory
    extensions_dir = os.path.join(plugin_dir, 'extensions')

    # Check if the extensions directory actually exists
    if os.path.isdir(extensions_dir):
        return extensions_dir
    else:
        return None


def get_version_information(event):
    '''Return version information for ftrack connect plugin.'''
    return [dict(name='ftrack-connect-publisher-widget', version=__version__)]


def register(session, **kw):
    '''Register plugin. Called when used as an plugin.'''
    # Validate that session is an instance of ftrack_api.Session. If not,
    # assume that register is being called from an old or incompatible API and
    # return without doing anything.
    if not isinstance(session, ftrack_api.session.Session):
        logger.debug(
            'Not subscribing plugin as passed argument {0!r} is not an '
            'ftrack_api.Session instance.'.format(session)
        )
        return

    handle_discovery_event = functools.partial(
        on_discover_integration, session
    )

    session.event_hub.subscribe(
        'topic=ftrack.connect.application.discover',
        handle_discovery_event,
        priority=20,
    )

    # Enable plugin info in Connect about dialog
    session.event_hub.subscribe(
        'topic=ftrack.connect.plugin.debug-information',
        get_version_information,
        priority=20,
    )
