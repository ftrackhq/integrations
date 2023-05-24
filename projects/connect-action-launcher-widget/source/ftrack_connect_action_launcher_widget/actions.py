# :coding: utf-8
# :copyright: Copyright (c) 2014 ftrack
import os
import json
import time
import logging
import functools
import qtawesome as qta

from ftrack_connect.qt import QtCore
from ftrack_connect.qt import QtWidgets
import ftrack_api.event.base
import ftrack_connect.asynchronous
import ftrack_connect.error
import ftrack_connect.usage

from ftrack_connect.ui.widget import (
    action_item,
    flow_layout,
    entity_selector,
    overlay,
)


class ActionBase(dict):
    '''Wrapper for an action dict.'''

    def __init__(self, *args, **kwargs):
        '''Initialise the action.'''
        super(ActionBase, self).__init__(*args, **kwargs)


class ActionSection(flow_layout.ScrollingFlowWidget):
    '''Action list view.'''

    #: Emitted before an action is launched with action
    beforeActionLaunch = QtCore.Signal(dict, name='beforeActionLaunch')

    #: Emitted after an action has been launched with action and results
    actionLaunched = QtCore.Signal(dict, list, name='actionLaunched')

    def clear(self):
        '''Remove all actions from section.'''
        items = self.findChildren(action_item.ActionItem)
        for item in items:
            # item.setParent(None)
            item.deleteLater()
            del item

    def addActions(self, actions):
        '''Add *actions* to section'''
        for item in actions:
            actionItem = action_item.ActionItem(
                self.session, item, parent=self
            )
            actionItem.actionLaunched.connect(self._onActionLaunched)
            actionItem.beforeActionLaunch.connect(self._onBeforeActionLaunched)
            self.addWidget(actionItem)

    def _onActionLaunched(self, action, results):
        '''Forward actionLaunched signal.'''
        self.actionLaunched.emit(action, results)

    def _onBeforeActionLaunched(self, action):
        '''Forward beforeActionLaunch signal.'''
        self.beforeActionLaunch.emit(action)


class Actions(QtWidgets.QWidget):
    '''Actions widget. Displays and runs actions with a selectable context.'''

    RECENT_METADATA_KEY = 'ftrack_recent_actions'
    RECENT_ACTIONS_LENGTH = 20
    ACTION_LAUNCH_MESSAGE_TIMEOUT = 1

    #: Emitted when recent actions has been modified
    recentActionsChanged = QtCore.Signal(name='recentActionsChanged')
    actionsLoaded = QtCore.Signal(object, name='actionsLoaded')
    actionsLoading = QtCore.Signal()

    @property
    def session(self):
        '''Return current session.'''
        return self._session

    def __init__(self, session, parent=None):
        '''Initiate a actions view.'''
        super(Actions, self).__init__(parent)

        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )
        self._session = session

        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)

        self._currentUserId = None
        self._recentActions = []
        self._actions = []

        self._entitySelector = entity_selector.EntitySelector(self.session)

        self._entitySelector.setFixedHeight(50)
        self._entitySelector.entityChanged.connect(self._onEntityChanged)
        layout.addWidget(QtWidgets.QLabel('Select action context'))
        layout.addWidget(self._entitySelector)

        self._recentLabel = QtWidgets.QLabel('Recent')
        layout.addWidget(self._recentLabel)
        self._recentSection = ActionSection(self.session, self)
        self._recentSection.setFixedHeight(150)
        self._recentSection.beforeActionLaunch.connect(
            self._onBeforeActionLaunched
        )
        self._recentSection.actionLaunched.connect(self._onActionLaunched)
        layout.addWidget(self._recentSection)

        self._allLabel = QtWidgets.QLabel('Discovering actions..')
        self._allLabel.setWordWrap(True)
        self._allLabel.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(self._allLabel)
        self._allSection = ActionSection(self.session, self)
        self._allSection.beforeActionLaunch.connect(
            self._onBeforeActionLaunched
        )
        self._allSection.actionLaunched.connect(self._onActionLaunched)
        layout.addWidget(self._allSection)

        self._overlay = overlay.BusyOverlay(
            parent=self, message='Launching...'
        )
        self._overlay.setVisible(False)

        self.recentActionsChanged.connect(self._updateRecentSection)

        self.actionsLoaded.connect(self.onActionsLoaded)
        self.actionsLoading.connect(self.onActionsLoading)

        context = self._contextFromEntity(self._entitySelector._entity)
        self._loadActionsForContext(context)
        self._updateRecentActions()

    def _onBeforeActionLaunched(self, action):
        '''Before action is launched, show busy overlay with message..'''
        self.logger.debug(u'Before action launched: {0}'.format(action))
        message = u'Launching action <em>{0} {1}</em>...'.format(
            action.get('label', 'Untitled action'), action.get('variant', '')
        )
        self._overlay.setMessage(message)
        self._overlay.indicator.show()
        self._overlay.setVisible(True)

    def _onActionLaunched(self, action, results):
        '''On action launched, save action and add it to top of list.'''
        self.logger.debug(u'Action launched: {0}'.format(action))
        self._addRecentAction(action['label'])
        self._moveToFront(self._recentActions, action['label'])
        self._updateRecentSection()

        self._showResultMessage(results)

        validMetadata = [
            'actionIdentifier',
            'label',
            'variant',
            'applicationIdentifier',
        ]
        metadata = {}
        for key, value in action.items():
            if key in validMetadata and value is not None:
                metadata[key] = value

        # Send usage event in the main thread to prevent X server threading
        # related crashes on Linux.
        ftrack_connect.usage.send_event(
            self.session, 'LAUNCHED-ACTION', metadata, asynchronous=False
        )

    def _showResultMessage(self, results):
        '''Show *results* message in overlay.'''
        message = 'Launched action'
        try:
            result = results[0]
            if 'items' in result.keys():
                message = (
                    'Custom UI for actions is not yet supported in Connect.'
                )
            else:
                message = result['message']
        except Exception:
            pass

        self._overlay.indicator.stop()
        self._overlay.indicator.hide()
        self._overlay.setMessage(message)
        self._hideOverlayAfterTimeout(self.ACTION_LAUNCH_MESSAGE_TIMEOUT)

    def _hideOverlayAfterTimeout(self, timeout):
        '''Hide overlay after *timeout* seconds.'''
        QtCore.QTimer.singleShot(
            timeout * 1000, functools.partial(self._overlay.setVisible, False)
        )

    def _contextFromEntity(self, entity):
        '''convert *entity* to list of dicts'''
        context = []
        if not entity:
            return context

        try:
            context = [
                {
                    'entityId': entity['id'],
                    'entityType': entity.entity_type.lower(),
                }
            ]
            self.logger.debug(u'Context changed: {0}'.format(context))
        except Exception:
            self.logger.debug(u'Invalid entity: {0}'.format(entity))

        return context

    def _onEntityChanged(self, entity):
        '''Load new actions when the context has changed'''
        context = self._contextFromEntity(entity)
        self._recentSection.clear()
        self._allSection.clear()
        self._updateRecentActions()
        self._loadActionsForContext(context)

    def _updateRecentSection(self):
        '''Clear and update actions in recent section.'''
        self._recentSection.clear()
        recentActions = []
        for recentAction in self._recentActions:
            for action in self._actions:
                if action[0]['label'] == recentAction:
                    recentActions.append(action)

        if recentActions:
            self._recentSection.addActions(recentActions)
            self._recentLabel.show()
            self._recentSection.show()
        else:
            self._recentLabel.hide()
            self._recentSection.hide()

    def _updateAllSection(self):
        '''Clear and update actions in all section.'''
        self._allSection.clear()
        if self._actions:
            self._allSection.addActions(self._actions)
            self._allLabel.setAlignment(QtCore.Qt.AlignLeft)
            self._allLabel.setText('All actions')
        else:
            self._allLabel.setAlignment(QtCore.Qt.AlignCenter)
            self._allLabel.setText(
                '<h2 style="font-weight: medium"> No matching applications or actions was found</h2>'
                '<p>Try another selection, add some actions and make sure you have the right integrations set up for the applications you want to launch.</p>'
            )

    def _updateRecentActions(self):
        '''Retrieve and update recent actions.'''
        self._recentActions = self._getRecentActions()
        self.recentActionsChanged.emit()

    def _getCurrentUserId(self):
        '''Return current user id.'''
        if not self._currentUserId:

            user = self.session.query(
                'User where username="{0}"'.format(self.session.api_user)
            ).one()
            self._currentUserId = user['id']

        return self._currentUserId

    def _getRecentActions(self):
        '''Retrieve recent actions from the server.'''

        metadata = self.session.query(
            'Metadata where key is "{0}" and parent_type is "User" '
            'and parent_id is "{1}"'.format(
                self.RECENT_METADATA_KEY, self._getCurrentUserId()
            )
        ).first()

        recentActions = []
        if metadata:
            try:
                recentActions = json.loads(metadata['value'])
            except ValueError as error:
                self.logger.warning(
                    'Error parsing metadata: {0}'.format(metadata)
                )
        return recentActions

    def _moveToFront(self, itemList, item):
        '''Prepend or move *item* to front of *itemList*.'''
        try:
            itemList.remove(item)
        except ValueError:
            pass
        itemList.insert(0, item)

    @ftrack_connect.asynchronous.asynchronous
    def _addRecentAction(self, actionLabel):
        '''Add *actionLabel* to recent actions, persisting the change.'''
        recentActions = self._getRecentActions()
        self._moveToFront(recentActions, actionLabel)
        recentActions = recentActions[: self.RECENT_ACTIONS_LENGTH]
        encodedRecentActions = json.dumps(recentActions)

        self.session.ensure(
            'Metadata',
            {
                'parent_type': 'User',
                'parent_id': self._getCurrentUserId(),
                'key': self.RECENT_METADATA_KEY,
                'value': encodedRecentActions,
            },
            identifying_keys=['parent_type', 'parent_id', 'key'],
        )

    # TODO: To re evaluate: breaks in PySide2 2.14, but works on PyQt5 2.15
    # @ftrack_connect.asynchronous.asynchronous
    def _loadActionsForContext(self, context):
        '''Obtain new actions synchronously for *context*.'''
        self.actionsLoading.emit()
        discoveredActions = []

        event = ftrack_api.event.base.Event(
            topic='ftrack.action.discover', data=dict(selection=context)
        )

        results = self.session.event_hub.publish(event, synchronous=True)

        for result in results:
            if result:
                for action in result.get('items', []):
                    discoveredActions.append(ActionBase(action))

        # Sort actions by label
        groupedActions = []
        for action in discoveredActions:
            action['selection'] = context
            added = False
            for groupedAction in groupedActions:
                if action['label'] == groupedAction[0]['label']:
                    groupedAction.append(action)
                    added = True

            if not added:
                groupedActions.append([action])

        # Sort actions by label
        groupedActions = sorted(
            groupedActions,
            key=lambda groupedAction: groupedAction[0]['label'].lower(),
        )

        self.actionsLoaded.emit(groupedActions)

    def onActionsLoaded(self, actions):
        self._actions = actions
        self._updateRecentSection()
        self._updateAllSection()
        self._overlay.indicator.hide()
        self._overlay.indicator.stop()
        self._overlay.setVisible(False)

    def onActionsLoading(self):
        message = u'Discovering Actions ....'
        self._overlay.setMessage(message)
        self._overlay.indicator.show()
        self._overlay.setVisible(True)
