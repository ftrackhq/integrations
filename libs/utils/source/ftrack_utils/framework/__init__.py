# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import os


def get_integration_session_id():
    return os.environ.get('FTRACK_INTEGRATION_SESSION_ID')
