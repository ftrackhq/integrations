#! /usr/bin/env python
# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack
import os

from ftrack_connect_pipeline_qt.client import QtClient
from ftrack_connect_pipeline_qt.ui.utility.widget.dialog import Dialog


class QtOpenClient(QtClient):
    '''
    Base open widget class.
    '''

    definition_filter = 'loader'
    client_name = 'open'

    def __init__(
        self, event_manager, definition_extensions_filter=None, parent=None
    ):
        if not definition_extensions_filter is None:
            self.definition_extensions_filter = definition_extensions_filter
        super(QtOpenClient, self).__init__(event_manager, parent=parent)
        self.logger.debug('start qt opener')

    def get_background_color(self):
        return 'ftrack'

    def post_build(self):
        super(QtOpenClient, self).post_build()
        self.context_selector.entityChanged.connect(self._store_global_context)

    def _store_global_context(self, entity):
        os.environ['FTRACK_CONTEXTID'] = entity['id']
        self.logger.warning('Global context is now: {}'.format(entity))

    def definition_changed(self, definition, available_components_count):
        '''React upon change of definition, or no versions/components(definitions) available.'''
        if available_components_count == 0:
            # We have no definitions or nothing previously published
            # TODO: Search among work files and see if there is and crash scene from previous session
            dlg = Dialog(
                question='Nothing to open, assemble a new scene?',
                parent=self,
            )
            if dlg.exec_():
                # Close and open assembler
                self.hide()
                raise NotImplementedError('Assembler open not implemented!')
        elif definition is not None and available_components_count == 1:
            dlg = Dialog(
                title=self.client_name.title(),
                question='Open latest?',
                parent=self,
            )
            if dlg.exec_():
                # Trig open
                self.run_button.click()
