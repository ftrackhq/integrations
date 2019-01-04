import os
import ftrack_api
import json
from ftrack_connect_pipeline import constants

cwd = os.path.dirname(__file__)


def register_asset(event):
    asset_dirs = os.getenv(constants.PIPELINE_ASSET_PATH_ENV) or os.path.join(cwd, '..', 'assets')
    files = os.listdir(asset_dirs)
    json_files = [file for file in files if file.endswith('json')]
    results = []
    for json_file in json_files:
        print 'registering :{}'.format(json_file)
        full_path = os.path.join(asset_dirs, json_file)
        with open(full_path, "r") as read_file:
            results.append(json.load(read_file))

    return results


def register(api_object, **kw):
    '''Register plugin to api_object.'''

    # Validate that api_object is an instance of ftrack_api.Session. If not,
    # assume that register_assets is being called from an incompatible API
    # and return without doing anything.
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return

    api_object.event_hub.subscribe(
        'topic={}'.format(constants.REGISTER_ASSET_TOPIC),
        register_asset
    )
