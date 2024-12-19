# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import threading
import functools
import sys


def asynchronous(method):
    '''Decorator to make a method asynchronous using its own thread.'''

    @functools.wraps(method)
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
            target=exceptHookWrapper, args=args, kwargs=kwargs
        )
        thread.name = str(method)
        thread.start()
        return thread

    return wrapper
