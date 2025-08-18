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


def get_latest_context_id(session):
    user = session.query(
        'User where username is "{0}"'.format(session.api_user)
    ).one()
    user_id = user['id']
    print(f"user_id : {user_id}")
    # Fetch the latest published context_id by the user
    query = (
        f'select context_id from AssetVersion where user_id is "{user_id}" '
        'and is_published is True order by date desc'
    )
    latest_version = session.query(query).first()
    print(f"latest_version : {latest_version}")

    if latest_version:
        return latest_version['context_id']

    # If no published context_id is found, fetch a valid accessible context_id for the user
    query = (
        f'select id from Context where ancestors.any(object_type="Project") '
        f'and tasks.responsible_users any (id="{user_id}") limit 1'
    )
    accessible_context = session.query(query).first()
    print(f"accessible_context : {accessible_context}")

    if accessible_context:
        return accessible_context['id']

    # If no context is found, raise an exception or handle as needed
    raise ValueError(f"No accessible context found for user with ID {user_id}")


def on_discover_integration(session):
    # TODO: Set the latest published task from the user as the context or an
    #  available one. With a function like the one above get_latest_context_id
    os.environ['FTRACK_CONTEXTID'] = '439dc504-a904-11ec-bbac-be6e0a48ed73'

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

    ftrack_framework_connect_widget.bootstrap_integration(
        session, get_extensions_path_from_environment()
    )


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

    on_discover_integration(session)

    # Enable plugin info in Connect about dialog
    session.event_hub.subscribe(
        'topic=ftrack.connect.plugin.debug-information',
        get_version_information,
        priority=20,
    )
