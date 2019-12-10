# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import threading
import sys
import logging

import os

from ftrack_connect_pipeline import constants


def get_current_context():
    '''return an api object representing the current context.'''
    context_id = os.getenv(
        'FTRACK_CONTEXTID',
            os.getenv('FTRACK_TASKID',
                os.getenv('FTRACK_SHOTID'
            )
        )
    )

    return context_id


def remote_event_mode():
    return bool(os.environ.get(
        constants.PIPELINE_REMOTE_EVENTS_ENV, 0
    ))
