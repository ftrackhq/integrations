# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

from QtExt import QtCore, QtWidgets
import logging

import ftrack
import ftrack_api.event.base

import ftrack_connect_pipeline.util
from ftrack_connect_pipeline.ui.widget.thumbnail import ActionIcon


class ActionItem(QtWidgets.QFrame):
    '''Widget representing an action item.'''

    #: Emitted before an action is launched with action
    beforeActionLaunch = QtCore.Signal(dict, name='beforeActionLaunch')

    #: Emitted after an action has been launched with action and results
    actionLaunched = QtCore.Signal(dict, list)

    def __init__(self, actions, session, parent=None):
        '''Initialize action item with *actions*.

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
        self.setObjectName('ftrack-action-item')
        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )
        self._session = session

        self.setMouseTracking(True)
        self.setFixedSize(QtCore.QSize(80, 70))
        layout = QtWidgets.QVBoxLayout()
        layout.setAlignment(QtCore.Qt.AlignCenter)
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
                action.get('variant', '')
            ).strip()
            for action in actions
        ]

        if len(actions) == 1:
            if actions[0].get('variant'):
                self._label = u'{0} {1}'.format(
                    self._label, actions[0].get('variant')
                )

            self._hoverIcon = 'play'
            self._multiple = False
        else:
            self._hoverIcon = 'menu'
            self._multiple = True

        self._iconLabel = ActionIcon(self)
        self._iconLabel.setAlignment(
            QtCore.Qt.AlignHCenter | QtCore.Qt.AlignBottom
        )
        self._iconLabel.setFixedSize(QtCore.QSize(80, 40))
        layout.addWidget(self._iconLabel)

        self._textLabel = QtWidgets.QLabel(self)
        self._textLabel.setObjectName('ftrack-action-item-label')
        self._textLabel.setAlignment(
            QtCore.Qt.AlignHCenter | QtCore.Qt.AlignTop
        )
        self._textLabel.setWordWrap(True)

        self._textLabel.setFixedSize(QtCore.QSize(80, 30))
        layout.addWidget(self._textLabel)

        self.setText(self._label)
        self.setIcon(self._icon)
        if self._description:
            self.setToolTip(self._description)

    def mouseReleaseEvent(self, event):
        '''Launch action on mouse release.

        First show menu with variants if multiple actions are available.
        '''
        if self._multiple:
            self.logger.debug('Launching menu to select action variant')
            menu = QtWidgets.QMenu(self)
            for index, variant in enumerate(self._variants):
                action = QtWidgets.QAction(variant, self)
                action.setData(index)
                menu.addAction(action)

            result = menu.exec_(QtWidgets.QCursor.pos())
            if result is None:
                return

            action = self._actions[result.data()]
        else:
            action = self._actions[0]

        self._launchAction(action)

    def enterEvent(self, event):
        '''Show hover icon on mouse enter.'''
        if self._multiple:
            self._iconLabel.loadResource(
                '{0}{1}'.format(':/ftrack/image/light/', self._hoverIcon)
            )

    def leaveEvent(self, event):
        '''Reset action icon on mouse leave.'''
        self.setIcon(self._icon)

    def setText(self, text):
        '''Set *text* on text label.'''
        self._textLabel.setText(text)

    def setIcon(self, icon):
        '''Set icon on icon label.'''
        self._iconLabel.setIcon(icon)

    def _launchAction(self, action):
        '''Launch *action* via event hub.'''
        self.logger.info(u'Launching action: {0}'.format(action))
        self.beforeActionLaunch.emit(action)
        self._publishLaunchActionEvent(action)

    @ftrack_connect_pipeline.util.asynchronous
    def _publishLaunchActionEvent(self, action):
        '''Launch *action* asynchronously and emit signal when completed.'''
        try:
            if action.is_new_api:
                session = self._session
                results = session.event_hub.publish(
                    ftrack_api.event.base.Event(
                        topic='ftrack.action.launch',
                        data=action
                    ),
                    synchronous=True
                )
            else:
                results = ftrack.EVENT_HUB.publish(
                    ftrack.Event(
                        topic='ftrack.action.launch',
                        data=action
                    ),
                    synchronous=True
                )

        except Exception as error:
            results = [{'success': False, 'message': 'Failed to launch action'}]
            self.logger.warning(
                u'Action launch failed with exception: {0}'.format(error)
            )

        self.logger.debug('Launched action with result: {0}'.format(results))
        self.actionLaunched.emit(action, results)
