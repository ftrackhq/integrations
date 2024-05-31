# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import ftrack_connect.ui.application

from ftrack_framework_connect_widget.connect_widget import (
    FrameworkConnectWidget,
)


# Dock widget in Connect
def dock_to_connect(session, widget):
    '''Dock *widget* to the right side of Maya.'''
    connect_widget = ftrack_connect.ui.application.ConnectWidgetPlugin(
        FrameworkConnectWidget(session, widget)
    )
    connect_widget.register(session, priority=20)
