# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

from ftrack_connect_pipeline_qt.client.open import QtOpenClient
import ftrack_connect_pipeline.constants as constants
import ftrack_connect_pipeline_qt.constants as qt_constants
import ftrack_connect_pipeline_maya.constants as maya_constants


class MayaOpenClient(QtOpenClient):
    ui_types = [constants.UI_TYPE, qt_constants.UI_TYPE, maya_constants.UI_TYPE]
    definition_extensions_filter = ['.mb', '.ma']

    '''Maya open dialog'''
    def __init__(self, event_manager, parent=None):
        super(MayaOpenClient, self).__init__(
            event_manager=event_manager, parent=parent
        )

