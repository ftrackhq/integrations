# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import logging
import copy

from ftrack_utils.server.track_usage import send_usage_event

logger = logging.getLogger('ftrack_utils:usage')

# Singleton instance placeholder
usage_tracker_singleton = None


def set_usage_tracker(usage_tracker):
    global usage_tracker_singleton
    if usage_tracker_singleton is None:
        usage_tracker_singleton = usage_tracker
    else:
        logger.error(
            "UsageTracker instance is already set. Ignoring the new instance."
        )


def get_usage_tracker():
    return usage_tracker_singleton


class UsageTracker:
    _instance = None

    def __new__(cls, session, default_data):
        if not cls._instance:
            cls._instance = super(UsageTracker, cls).__new__(cls)
            # Initialize the instance only once
            cls._instance._session = session
            cls._instance._default_data = default_data
        return cls._instance

    def track(self, event_name, metadata):
        # To not modify the default metadata dictionary instance, we do a deep copy of it.
        default_metadata = copy.deepcopy(self._default_data)
        default_metadata.update(metadata)
        send_usage_event(
            self._session,
            event_name,
            default_metadata,
            asynchronous=True,
        )
        logger.debug(
            f"Tracking: event_name: {event_name}, metadata: {metadata}"
        )
