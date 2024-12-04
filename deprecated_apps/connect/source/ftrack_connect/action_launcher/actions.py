# :coding: utf-8
# :copyright: Copyright (c) 2014-2024 ftrack
import json
import logging
import functools
import platform

try:
    from PySide6 import QtWidgets, QtCore
except ImportError:
    from PySide2 import QtWidgets, QtCore

import ftrack_api.event.base
from ftrack_utils.decorators import asynchronous
from ftrack_utils.usage import get_usage_tracker

from ftrack_connect.ui.widget import (
    action_item,
    flow_layout,
    entity_selector,
    overlay,
)

from ftrack_connect.utils.preferences import (
    get_connect_preferences,
    write_connect_prefs_file_path,
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

    def add_actions(self, actions):
        '''Add *actions* to section'''
        for item in actions:
            item = action_item.ActionItem(self.session, item, parent=self)
            item.actionLaunched.connect(self._on_action_launched_callback)
            item.beforeActionLaunch.connect(
                self._on_before_action_launched_callback
            )
            self.addWidget(item)

    def _on_action_launched_callback(self, action, results):
        '''Forward actionLaunched signal.'''
        self.actionLaunched.emit(action, results)

    def _on_before_action_launched_callback(self, action):
        '''Forward beforeActionLaunch signal.'''
        self.beforeActionLaunch.emit(action)


class Actions(QtWidgets.QWidget):
    '''Actions widget. Displays and runs actions with a selectable context.'''

    RECENT_METADATA_KEY = 'ftrack_recent_actions'
    RECENT_ACTIONS_LENGTH = 20
    ACTION_LAUNCH_MESSAGE_TIMEOUT = 3

    #: Emitted when recent actions has been modified
    recent_actions_changed = QtCore.Signal(name='recentActionsChanged')
    actions_loaded = QtCore.Signal(object, name='actionsLoaded')
    actions_loading = QtCore.Signal()

    @property
    def session(self):
        '''Return current session.'''
        return self._session

    @property
    def actions(self):
        '''Return actions.'''
        return self._actions

    def __init__(self, session, parent=None):
        '''Initiate a actions view.'''
        super(Actions, self).__init__(parent)

        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )
        self._session = session

        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)

        self._current_user_id = None
        self._recent_actions = []
        self._actions = []

        self._entity_selector = entity_selector.EntitySelector(self.session)

        self._entity_selector.setFixedHeight(50)
        self._entity_selector.entityChanged.connect(self._on_entity_changed)
        layout.addWidget(QtWidgets.QLabel('Select action context'))
        layout.addWidget(self._entity_selector)

        self._recent_label = QtWidgets.QLabel('Recent')
        layout.addWidget(self._recent_label)
        self._recent_section = ActionSection(self.session, self)
        self._recent_section.setFixedHeight(150)
        self._recent_section.beforeActionLaunch.connect(
            self._on_before_action_launched_callback
        )
        self._recent_section.actionLaunched.connect(
            self._on_action_launched_callback
        )
        layout.addWidget(self._recent_section)

        self._all_label = QtWidgets.QLabel('Discovering actions..')
        self._all_label.setWordWrap(True)
        self._all_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._all_label)
        self._all_section = ActionSection(self.session, self)
        self._all_section.beforeActionLaunch.connect(
            self._on_before_action_launched_callback
        )
        self._all_section.actionLaunched.connect(
            self._on_action_launched_callback
        )
        layout.addWidget(self._all_section)

        self._overlay = overlay.BusyOverlay(
            parent=self, message='Launching...'
        )
        self._overlay.setVisible(False)

        self.recent_actions_changed.connect(self._update_recent_section)

        self.actions_loaded.connect(self._on_actions_loaded_callback)
        self.actions_loading.connect(self._on_actions_loading_callback)

        context = self._context_from_entity(self._entity_selector._entity)
        self._load_actions_for_context(context)
        self._update_recent_actions()

    def _on_before_action_launched_callback(self, action):
        '''Before action is launched, show busy overlay with message..'''
        self.logger.debug(f'Before action launched: {action}')

        rise_message = None
        launcher_prefs = get_connect_preferences()
        known_rosetta_apps = launcher_prefs.get('known_rosetta_apps', [])
        if (
            platform.system().lower() == 'darwin'
            and action.get('rosetta')
            and action['actionIdentifier'] not in known_rosetta_apps
        ):
            import subprocess

            # Execute the 'sysctl' command to check for ARM64 support
            result = subprocess.run(
                ["sysctl", "-n", "hw.optional.arm64"],
                capture_output=True,
                text=True,
            )

            # Check if the output is silicon.
            if result.stdout.strip() == '1':
                rise_message = (
                    'You are on Apple silicon computer, the '
                    'integration for the application you are launching '
                    'requires to be launched using Rosetta. '
                    'Please set "opening using Rosetta" checkbox '
                    'on your app before launching or change the '
                    'launch configuration. Get More info at: '
                    'https://support.apple.com/en-us/HT211861#needsrosetta'
                )
                self.logger.debug(rise_message)

        if rise_message:
            message_box = QtWidgets.QMessageBox(
                QtWidgets.QMessageBox.Icon.Warning,
                'Warning',
                rise_message,
                buttons=QtWidgets.QMessageBox.Ok,
            )
            # Create the checkbox
            checkbox = QtWidgets.QCheckBox("Don't show this message again.")
            message_box.setCheckBox(checkbox)

            response = message_box.exec_()
            # Check if OK was clicked and if the checkbox was checked
            if response == QtWidgets.QMessageBox.Ok:
                if checkbox.isChecked():
                    known_rosetta_apps.append(action['actionIdentifier'])
                    launcher_prefs['known_rosetta_apps'] = known_rosetta_apps
                    write_connect_prefs_file_path(launcher_prefs)

        message = (
            f'Launching action <em>{action.get("label", "Untitled action")} '
            f'{action.get("variant", "")}</em>...'
        )
        self._overlay.message = message
        self._overlay.indicator.show()
        self._overlay.setVisible(True)

    def _on_action_launched_callback(self, action, results):
        '''On action launched, save action and add it to top of list.'''
        self.logger.debug(f'Action launched: {action}')
        self._add_recent_action(action['label'])
        self._move_to_front(self._recent_actions, action['label'])
        self._update_recent_section()

        self._show_result_message(results)

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
        usage_tracker = get_usage_tracker()
        if usage_tracker:
            usage_tracker.track("LAUNCHED-CONNECT-ACTION", metadata)

    def _show_result_message(self, results):
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
        self._overlay.message = message
        self._hide_overlay_after_timeout(self.ACTION_LAUNCH_MESSAGE_TIMEOUT)

    def _hide_overlay_after_timeout(self, timeout):
        '''Hide overlay after *timeout* seconds.'''
        QtCore.QTimer.singleShot(
            timeout * 1000, functools.partial(self._overlay.setVisible, False)
        )

    def _context_from_entity(self, entity):
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
            self.logger.debug(f'Context changed: {context}')
        except Exception:
            self.logger.debug(f'Invalid entity: {entity}')

        return context

    def _on_entity_changed(self, entity):
        '''Load new actions when the context has changed'''
        context = self._context_from_entity(entity)
        self._recent_section.clear()
        self._all_section.clear()
        self._update_recent_actions()
        self._load_actions_for_context(context)

    def _update_recent_section(self):
        '''Clear and update actions in recent section.'''
        self._recent_section.clear()
        recent_actions = []
        for recentAction in self._recent_actions:
            for action in self._actions:
                if action[0]['label'] == recentAction:
                    recent_actions.append(action)

        if recent_actions:
            self._recent_section.add_actions(recent_actions)
            self._recent_label.show()
            self._recent_section.show()
        else:
            self._recent_label.hide()
            self._recent_section.hide()

    def _update_all_section(self):
        '''Clear and update actions in all section.'''
        self._all_section.clear()
        if self._actions:
            self._all_section.add_actions(self._actions)
            self._all_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft)
            self._all_label.setText('All actions')
        else:
            self._all_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            self._all_label.setText(
                '<h2 style="font-weight: medium"> No matching applications or actions was found</h2>'
                '<p>Try another selection, add some actions and make sure you have the right integrations set up for the applications you want to launch.</p>'
            )

    def _update_recent_actions(self):
        '''Retrieve and update recent actions.'''
        self._recent_actions = self._get_recent_actions()
        self.recent_actions_changed.emit()

    def _get_current_user_id(self):
        '''Return current user id.'''
        if not self._current_user_id:
            user = self.session.query(
                f'User where username="{self.session.api_user}"'
            ).one()
            self._current_user_id = user['id']

        return self._current_user_id

    def _get_recent_actions(self):
        '''Retrieve recent actions from the server.'''

        metadata = self.session.query(
            f'Metadata where key is "{self.RECENT_METADATA_KEY}" and parent_type is "User" '
            f'and parent_id is "{self._get_current_user_id()}"'
        ).first()

        recent_actions = []
        if metadata:
            try:
                recent_actions = json.loads(metadata['value'])
            except ValueError as e:
                self.logger.warning(f'Error parsing metadata {metadata}: {e}')
        return recent_actions

    def _move_to_front(self, item_list, item):
        '''Prepend or move *item* to front of *itemList*.'''
        try:
            item_list.remove(item)
        except ValueError:
            pass
        item_list.insert(0, item)

    @asynchronous
    def _add_recent_action(self, action_label):
        '''Add *actionLabel* to recent actions, persisting the change.'''
        recent_actions = self._get_recent_actions()
        self._move_to_front(recent_actions, action_label)
        recent_actions = recent_actions[: self.RECENT_ACTIONS_LENGTH]
        encoded_recent_actions = json.dumps(recent_actions)

        self.session.ensure(
            'Metadata',
            {
                'parent_type': 'User',
                'parent_id': self._get_current_user_id(),
                'key': self.RECENT_METADATA_KEY,
                'value': encoded_recent_actions,
            },
            identifying_keys=['parent_type', 'parent_id', 'key'],
        )

    # TODO: To re evaluate: breaks in PySide2 2.14, but works on PyQt5 2.15
    # @asynchronous
    def _load_actions_for_context(self, context):
        '''Obtain new actions synchronously for *context*.'''
        self.actions_loading.emit()
        discovered_actions = []

        event = ftrack_api.event.base.Event(
            topic='ftrack.action.discover', data=dict(selection=context)
        )

        results = self.session.event_hub.publish(event, synchronous=True)

        for result in results:
            if result:
                for action in result.get('items', []):
                    discovered_actions.append(ActionBase(action))

        # Sort actions by label
        grouped_actions = []
        for action in discovered_actions:
            action['selection'] = context
            added = False
            for groupedAction in grouped_actions:
                if action['label'] == groupedAction[0]['label']:
                    groupedAction.append(action)
                    added = True

            if not added:
                grouped_actions.append([action])

        # Sort actions by label
        grouped_actions = sorted(
            grouped_actions,
            key=lambda grouped_action: grouped_action[0]['label'].lower(),
        )

        self.actions_loaded.emit(grouped_actions)

    def _on_actions_loaded_callback(self, actions):
        self._actions = actions
        self._update_recent_section()
        self._update_all_section()
        self._overlay.indicator.hide()
        self._overlay.indicator.stop()
        self._overlay.setVisible(False)

    def _on_actions_loading_callback(self):
        message = u'Discovering Actions ....'
        self._overlay.message = message
        self._overlay.indicator.show()
        self._overlay.setVisible(True)
