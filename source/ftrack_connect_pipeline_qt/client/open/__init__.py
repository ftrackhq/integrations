#! /usr/bin/env python
# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

import os

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
        self.logger.debug('start qt opener')

    def post_build(self):
        super(QtOpenClient, self).post_build()
        self.context_selector.entityChanged.connect(self._store_global_context)

    def _store_global_context(self, entity):
        os.environ['FTRACK_CONTEXT_ID'] = entity['id']
        self.logger.warning('Global context is now: {}'.format(entity))