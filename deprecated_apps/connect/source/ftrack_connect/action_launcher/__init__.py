# :coding: utf-8
# :copyright: Copyright (c) 2014-2024 ftrack

try:
    from PySide6 import QtWidgets
except ImportError:
    from PySide2 import QtWidgets

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

    def get_debug_information(self):
        '''Append all launch actions as debug information.'''
        result = super(ActionLauncherWidget, self).get_debug_information()
        result['available_actions'] = []
        for action in self._actions_view.actions:
            result['available_actions'].append(action)
        return result
