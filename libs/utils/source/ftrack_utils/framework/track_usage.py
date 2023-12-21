# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from ftrack_utils.server.track_usage import send_usage_event


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

    # Leaving this here for debugging purposes.
    # Will be removed in further iterations.
    # print(f"Tracking: {label}, {module}, {version}, {os}")
