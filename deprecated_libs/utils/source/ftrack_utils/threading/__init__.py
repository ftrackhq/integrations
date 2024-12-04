# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

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
