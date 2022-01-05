#! /usr/bin/env python
# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack


from ftrack_connect_pipeline_qt.client import QtClient


class QtOpenClient(QtClient):
    '''
    Base load widget class.
    '''
    definition_filter = 'loader'
    run_definition_button_text = 'Open'

    def __init__(self, event_manager, definition_extensions_filter=None, parent=None):
        if not definition_extensions_filter is None:
            self.definition_extensions_filter = definition_extensions_filter
        super(QtOpenClient, self).__init__(
            event_manager, parent=parent
        )
        self.setWindowTitle('Standalone Pipeline Opener')
        self.logger.debug('start qt opener')
        self.resize(450, 500)