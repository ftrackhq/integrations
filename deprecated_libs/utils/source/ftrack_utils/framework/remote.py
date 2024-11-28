# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack
import os


def get_remote_integration_session_id():
    '''Return the session ID shared with a driven RPC integration, in
    standalone mode.'''
    return os.environ.get('FTRACK_REMOTE_INTEGRATION_SESSION_ID')
