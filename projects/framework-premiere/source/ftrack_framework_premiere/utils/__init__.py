# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack
import logging
import os.path
import socket

from ftrack_utils.rpc import JavascriptRPC

logger = logging.getLogger(__name__)


def get_premiere_session_identifier():
    '''Get the name of the current open file in Premiere'''
    computer_name = socket.gethostname()
    identifier = '{}_Premiere_%s' % computer_name

    # Get existing RPC connection instance
    premiere_connection = JavascriptRPC.instance()

    # Get document data containing the path
    try:
        project_path = premiere_connection.rpc('getProjectPath')

        if not project_path or project_path.startswith('Error:'):
            logger.warning(f'Unable to  get project path: {project_path}')
            identifier = identifier.format(os.path.basename('Untitled'))
        else:
            identifier = identifier.format(
                os.path.splitext(project_path.split('/')[-1])[0]
            )
    except Exception as e:
        logger.exception(e)
        identifier = identifier.format('?')

    return identifier
