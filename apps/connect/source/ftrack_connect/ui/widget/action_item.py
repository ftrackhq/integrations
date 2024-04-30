# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import os
import logging

import qtawesome as qta

try:
    from PySide6 import QtWidgets, QtCore, QtGui
    from PySide6.QtGui import QAction
except ImportError:
    from PySide2 import QtWidgets, QtCore, QtGui
    from PySide2.QtWidgets import QAction

import ftrack_api.event.base
from ftrack_utils.decorators import asynchronous
from ftrack_connect.ui.widget.thumbnail import ActionIcon

# We need to force load the icons or ftrack.<icon> won't be available
# not sure why is the case, likely due to be in threded function.


class ActionItem(QtWidgets.QFrame):
    '''Widget representing an action item.'''

    #: Emitted before an action is launched with action
    beforeActionLaunch = QtCore.Signal(dict, name='beforeActionLaunch')

    #: Emitted after an action has been launched with action and results
    actionLaunched = QtCore.Signal(dict, list)

    @property
    def session(self):
        '''Return current session.'''
        return self._session

    def __init__(self, session, actions, parent=None):
        '''Initialize action item with *actions*

        *actions* should be a list of action dictionaries with the same label.
        Each action may contain a the following:

        label
            To be displayed as text
        icon
            An URL to an image or one of the provided icons.
        variant
            A variant of the action. Will be shown in the menu shown for
            multiple actions, or as part of the label for a single action.
        description
            A optional description of the action to be shown on hover.

        Label, icon and description will be retrieved from the first action if
        multiple actions are specified.
        '''
        super(ActionItem, self).__init__(parent=parent)
        self._session = session
        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )

        self.setMouseTracking(True)
        self.setFixedSize(QtCore.QSize(75, 105))
        layout = QtWidgets.QVBoxLayout()
        layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        if not actions:
            raise ValueError('No actions specified')

        self._actions = actions
        self._label = actions[0].get('label', 'Untitled action')
        self._icon = actions[0].get('icon', None)
        self._description = actions[0].get('description', None)
        self._variants = [
            u'{0} {1}'.format(
                action.get('label', 'Untitled action'),
                action.get('variant', ''),
            ).strip()
            for action in actions
        ]

        if len(actions) == 1:
            if actions[0].get('variant'):
                self._label = u'{0} {1}'.format(
                    self._label, actions[0].get('variant')
                )

            self._hoverIcon = None
            self._multiple = False
        else:
            self._hoverIcon = 'menu'
            self._multiple = True

        self.action_icon = qta.icon('ftrack.actions')
        self._iconLabel = ActionIcon(self, default_icon=self.action_icon)
        self._iconLabel.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self._iconLabel.setFixedSize(QtCore.QSize(75, 45))
        layout.addWidget(self._iconLabel)

        self._textLabel = QtWidgets.QLabel(self)
        self._textLabel.setAlignment(
            QtCore.Qt.AlignmentFlag.AlignHCenter
            | QtCore.Qt.AlignmentFlag.AlignTop
        )
        self._textLabel.setContentsMargins(0, 5, 0, 0)
        self._textLabel.setWordWrap(True)
        self._textLabel.setFixedSize(QtCore.QSize(75, 55))
        layout.addWidget(self._textLabel)

        self.setText(self._label)
        self.setIcon(self._icon)

        if self._description:
            self.setToolTip(self._description)

        self.setObjectName('action-item')
        self.setState()

    def setState(self, state='inactive'):
        self.setProperty('state', state)
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()

    def mouseReleaseEvent(self, event):
        '''Launch action on mouse release.

        First show menu with variants if multiple actions are available.
        '''
        self.setState('active')
        if self._multiple:
            self.logger.debug('Launching menu to select action variant')
            menu = QtWidgets.QMenu(self)
            for index, variant in enumerate(self._variants):
                action = QAction(variant, self)
                action.setData(index)
                menu.addAction(action)

            result = menu.exec_(QtGui.QCursor.pos())
            if result is None:
                return

            action = self._actions[result.data()]
        else:
            action = self._actions[0]

        self._launchAction(action)

    def enterEvent(self, event):
        '''Show hover icon on mouse enter.'''
        self.setState('active')
        if self._hoverIcon:
            self.setIcon(qta.icon('mdi.{}'.format(self._hoverIcon)))

    def leaveEvent(self, event):
        '''Reset action icon on mouse leave.'''
        self.setIcon(self._icon)
        self.setState()

    def setText(self, text):
        '''Set *text* on text label.'''
        self._textLabel.setText(text)

    def setIcon(self, icon):
        '''Set icon on icon label.'''
        self._iconLabel.setIcon(icon)

    def _launchAction(self, action):
        '''Launch *action* via event hub.'''
        self.logger.debug(u'Launching action: {0}'.format(action))
        self.beforeActionLaunch.emit(action)
        self._publishLaunchActionEvent(action)

    @asynchronous
    def _publishLaunchActionEvent(self, action):
        '''Launch *action* asynchronously and emit *actionLaunched* when completed.'''

        try:
            results = self.session.event_hub.publish(
                ftrack_api.event.base.Event(
                    topic='ftrack.action.launch', data=action
                ),
                synchronous=True,
            )

        except Exception as error:
            results = [
                {'success': False, 'message': 'Failed to launch action'}
            ]
            self.logger.warning(
                u'Action launch failed with exception: {0}'.format(error)
            )

        self.logger.debug('Launched action with result: {0}'.format(results))
        self.actionLaunched.emit(action, results)
