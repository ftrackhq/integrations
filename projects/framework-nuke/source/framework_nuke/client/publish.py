# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

from Qt import QtWidgets, QtCore

from framework_qt.client.publish import QtPublisherClientWidget
import framework_core.constants as constants
import framework_qt.constants as qt_constants
import framework_nuke.constants as nuke_constants


class NukeQtPublisherClientWidget(QtPublisherClientWidget):
    ui_types = [
        constants.UI_TYPE,
        qt_constants.UI_TYPE,
        nuke_constants.UI_TYPE,
    ]

    '''Dockable nuke publish widget'''

    def __init__(self, event_manager):
        super(NukeQtPublisherClientWidget, self).__init__(event_manager)

    def get_theme_background_style(self):
        return 'nuke'

    def hideEvent(self, *args, **kwargs):
        super(NukeQtPublisherClientWidget, self).hideEvent(*args, **kwargs)
        self.logger.debug('closing qt client')
        # Unsubscribe to context change events
        self.unsubscribe_host_context_change()
