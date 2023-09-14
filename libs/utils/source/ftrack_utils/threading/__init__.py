# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import os
import threading


class BaseThread(threading.Thread):
    '''Thread helper class providing callback functionality'''

    def __init__(self, callback=None, target_args=None, *args, **kwargs):
        target = kwargs.pop('target')
        super(BaseThread, self).__init__(
            target=self.target_with_callback, *args, **kwargs
        )
        self.callback = callback
        self.method = target
        self.target_args = target_args

    def target_with_callback(self):
        result = self.method(*self.target_args)
        if self.callback is not None:
            self.callback(result)


def multithreading_enabled():
    '''Return True if multithreading is enabled. This environment variable should be
    set to "false" when launching a DCC that is not capable of multithreading - e.g.
    provide methods for running async tasks in main thread providing UX experience
    benefits such as spinners, progress widgets and other realtime feedback.'''
    return 'FTRACK_FRAMEWORK_MULTITHREADING' not in os.environ or os.environ[
        'FTRACK_FRAMEWORK_MULTITHREADING'
    ].lower().strip() in ["true", "1"]
