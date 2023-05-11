# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

from ftrack_connect_pipeline_qt.client.publish import QtPublisherClientWidget
import ftrack_connect_pipeline.constants as constants
import ftrack_connect_pipeline_qt.constants as qt_constants
import ftrack_connect_pipeline_maya.constants as maya_constants

from maya.app.general.mayaMixin import MayaQWidgetDockableMixin


class MayaQtPublisherClientWidget(QtPublisherClientWidget):
    def __init__(self, event_manager, parent=None):
        '''Due to the Maya panel behaviour, we have to use *parent_window*
        instead of *parent*.'''
        super(MayaQtPublisherClientWidget, self).__init__(event_manager)


class MayaQtPublisherClientWidgetMixin(
    MayaQWidgetDockableMixin, MayaQtPublisherClientWidget
):
    ui_types = [
        constants.UI_TYPE,
        qt_constants.UI_TYPE,
        maya_constants.UI_TYPE,
    ]

    '''Dockable maya publish widget'''

    def __init__(self, event_manager):
        super(MayaQtPublisherClientWidgetMixin, self).__init__(
            event_manager=event_manager
        )

    def get_theme_background_style(self):
        return 'maya'

    def show(self):
        super(MayaQtPublisherClientWidgetMixin, self).show(
            dockable=True,
            floating=False,
            area='right',
            width=200,
            height=300,
            x=300,
            y=600,
            retain=False,
        )

    def dockCloseEventTriggered(self):
        super(MayaQtPublisherClientWidgetMixin, self).dockCloseEventTriggered()
        self.logger.debug('closing qt client')
        # Unsubscribe to context change events
        self.unsubscribe_host_context_change()
