# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack
import logging
import os.path
import socket

from ftrack_utils.rpc import JavascriptRPC

logger = logging.getLogger(__name__)


def get_photoshop_session_identifier():
    '''Get the name of the current open file in Photoshop'''
    computer_name = socket.gethostname()
    identifier = '{}_Photoshop_%s' % computer_name

    # Get existing RPC connection instance
    photoshop_connection = JavascriptRPC.instance()

    # Get document data containing the path
    try:
        document_data = photoshop_connection.rpc('getDocumentData')

        if 'full_path' in document_data:
            identifier = identifier.format(
                document_data['full_path'].split('/')[-1]
            )
        else:
            identifier = identifier.format(os.path.basename('Untitled'))
    except Exception as e:
        logger.exception(e)
        identifier = identifier.format('?')

    return identifier
