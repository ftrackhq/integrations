
import os
import ftrack_api

_shared_session = None

def get_shared_session(plugin_paths=None):
    '''Return shared ftrack_api session.'''
    global _shared_session

    if not _shared_session:
        # Create API session using credentials as stored by the application
        # when logging in.
        _shared_session = ftrack_api.Session(
            server_url=os.environ['FTRACK_SERVER'],
            api_key=os.environ['FTRACK_API_KEY'],
            api_user=os.environ['FTRACK_API_USER'],
            plugin_paths=plugin_paths
        )

    return _shared_session
