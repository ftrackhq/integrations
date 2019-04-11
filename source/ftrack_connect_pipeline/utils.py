import os
from ftrack_connect_pipeline import constants


def remote_event_mode():
    return bool(os.environ.get(
        constants.PIPELINE_REMOTE_EVENTS_ENV, 0
    ))
