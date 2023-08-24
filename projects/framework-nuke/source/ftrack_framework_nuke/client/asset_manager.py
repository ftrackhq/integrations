# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from Qt import QtWidgets, QtCore

from ftrack_framework_qt.client.asset_manager import (
    QtAssetManagerClientWidget,
)
import ftrack_framework_core.constants as constants
import ftrack_framework_qt.constants as qt_constants
import ftrack_framework_nuke.constants as nuke_constants


class NukeQtAssetManagerClientWidget(QtAssetManagerClientWidget):
    ui_types = [
        constants.UI_TYPE,
        qt_constants.UI_TYPE,
        nuke_constants.UI_TYPE,
    ]

    '''Dockable nuke asset manager widget'''

    def __init__(self, event_manager, asset_list_model):
        super(NukeQtAssetManagerClientWidget, self).__init__(
            event_manager, asset_list_model
        )

    def get_theme_background_style(self):
        return 'nuke'

    def hideEvent(self, *args, **kwargs):
        super(NukeQtAssetManagerClientWidget, self).hideEvent(*args, **kwargs)
        self.logger.debug('closing qt client')
        # Unsubscribe to context change events
        self.unsubscribe_host_context_change()
