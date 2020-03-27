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


def asynchronous(method):
    '''Decorator to make a method asynchronous using its own thread.'''

    def wrapper(*args, **kwargs):
        '''Thread wrapped method.'''

        def exceptHookWrapper(*args, **kwargs):
            '''Wrapp method and pass exceptions to global excepthook.

            This is needed in threads because of
            https://sourceforge.net/tracker/?func=detail&atid=105470&aid=1230540&group_id=5470
            '''
            try:
                method(*args, **kwargs)
            except (KeyboardInterrupt, SystemExit):
                raise
            except:
                sys.excepthook(*sys.exc_info())

        thread = threading.Thread(
            target=exceptHookWrapper,
            args=args,
            kwargs=kwargs
        )
        thread.start()

    return wrapper