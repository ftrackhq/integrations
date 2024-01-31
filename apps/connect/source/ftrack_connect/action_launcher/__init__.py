# :coding: utf-8
# :copyright: Copyright (c) 2014-2024 ftrack

from ftrack_connect.qt import QtWidgets

from ftrack_connect.ui.application import ConnectWidget
from ftrack_connect.action_launcher.actions import Actions


class ActionLauncherWidget(ConnectWidget):
    name = 'Launch'

    def __init__(self, session, parent=None):
        '''Instantiate the actions widget.'''
        super(ActionLauncherWidget, self).__init__(session, parent=parent)
        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)

        self._actions_view = Actions(self.session)
        layout.addWidget(self._actions_view)
