# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

from ftrack_framework_qt.client.publish import QtPublisherClientWidget
import ftrack_framework_core.constants as constants
import ftrack_framework_qt.constants as qt_constants
import ftrack_framework_maya.constants as maya_constants

from maya.app.general.mayaMixin import MayaQWidgetDockableMixin

# TODO: we will have all the logic in the core, except for the overrides.
#  class mayapublisher(client):
#      widget=None
#  class mayapublisherwidget(mayapublisher, MayaQWidgetDockableMixin):
#     widget = qt.framework.publisher_widget # --> this widget inherits from ABC framework_ui and from the qtwidget
#     if widget:
#        self.layout.addWidget(widget)


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
