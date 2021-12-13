#! /usr/bin/env python
# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack


from ftrack_connect_pipeline_qt.client import QtClient


class QtLoaderClient(QtClient):
    '''
    Base load widget class.
    '''
    definition_filter = 'loader'
    run_definition_button_text = 'Load'

    def __init__(self, event_manager, parent=None):

        super(QtLoaderClient, self).__init__(
            event_manager, parent=parent
        )
        self.setWindowTitle('Standalone Pipeline Loader')
        self.logger.debug('start qt loader')

        self.setProperty('background', 'styled')