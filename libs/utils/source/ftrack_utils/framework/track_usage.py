# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import logging

from ftrack_utils.server.track_usage import send_usage_event


logger = logging.getLogger('ftrack_utils:usage')


def ftrack_framework_usage(session, label, module, version, os):
    '''Track usage of the framework.'''
    metadata = {
        'label': label,
        'module': module,
        'version': version,
        'os': os,
    }

    send_usage_event(
        session,
        'USED-INTEGRATION-FRAMEWORK',
        metadata,
        asynchronous=True,
    )

    logger.debug(f"Tracking: {label}, {module}, {version}, {os}")
