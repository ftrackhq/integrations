#! /usr/bin/env python
# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack


from ftrack_connect_pipeline_qt.client import QtClient


class QtPublisherClient(QtClient):
    '''
    Base load widget class.
    '''

    def __init__(self, event_manager, ui=None, parent=None):
        super(QtPublisherClient, self).__init__(event_manager, ui=ui,
                                                parent=parent)
        self.setWindowTitle('Standalone Pipeline Publisher')
        self.logger.info('start qt publisher')
