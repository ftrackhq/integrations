# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

from Qt import QtCore

from ftrack_connect_pipeline import constants as core_constants
from ftrack_connect_pipeline_qt import constants as qt_constants


class QtWidgetMixin:
    '''Minimal QT client class handling async processing of host callbacks'''

    ui_types = [core_constants.UI_TYPE, qt_constants.UI_TYPE]

    contextChanged = QtCore.Signal(object)  # Context has changed

    def __init__(self):
        self.contextChanged.connect(self.on_context_changed_sync)

    def on_context_changed(self, context_id):
        '''Async call upon context changed'''
        self.contextChanged.emit(context_id)

    def closeEvent(self, e):
        super(QtWidgetMixin, self).closeEvent(e)
        # Unsubscribe to events
        if self.context_change_subscribe_id:
            self.logger.debug('closing qt client')
            self.session.event_hub.unsubscribe(
                self.context_change_subscribe_id
            )
