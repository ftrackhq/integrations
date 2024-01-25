# :coding: utf-8
# :copyright: Copyright (c) 2014-2024 ftrack
import platform
import traceback
import qtawesome as qta

from ftrack_connect.qt import QtWidgets, QtCore, QtGui

from ftrack_connect.ui.widget.overlay import BlockingOverlay, BusyOverlay
import ftrack_connect.ui.application

from ftrack_utils.decorators import asynchronous
from ftrack_utils.server import send_usage_event

from ftrack_connect.plugin_manager.overlay import InstallerBlockingOverlay
from ftrack_connect.plugin_manager.processor import PluginProcessor, ROLES
from ftrack_connect.plugin_manager.pluginlist import DndPluginList
from ftrack_connect.plugin_manager.welcome import WelcomeDialog


class PluginManager(ftrack_connect.ui.application.ConnectWidget):
    '''Show and manage plugin installations.'''

    name = 'Plugins'

    show_welcome = QtCore.Signal()

    installation_done = QtCore.Signal()
    installation_started = QtCore.Signal()
    installation_in_progress = QtCore.Signal(object)
    installation_failed = QtCore.Signal(object)

    refresh_started = QtCore.Signal()
    refresh_done = QtCore.Signal()

    apply_changes = QtCore.Signal(object)
    # List of plugins to archive as argument

    # default methods
    def __init__(self, session, parent=None):
        '''Instantiate the plugin widget.'''
        super(PluginManager, self).__init__(session, parent=parent)
        self._label = None
        self._search_bar = None
        self._plugin_list_widget = None
        self._button_layout = None
        self._apply_button = None
        self._reset_button = None
        self._welcome_dialog = None
        self._blocking_overlay = None
        self._busy_overlay = None
        self._plugins_to_install = None
        self._counter = 0

        self._reset_plugin_list()
        self._plugin_processor = PluginProcessor()

        self.pre_build()
        self.build()
        self.post_build()

        # refresh
        self._refresh(True)

    def pre_build(self):
        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)

    def build(self):
        self._search_bar = QtWidgets.QLineEdit()
        self._search_bar.setPlaceholderText('Search plugin...')

        self.layout().addWidget(self._search_bar)
        self._label = QtWidgets.QLabel(
            'Check the plugins you want to install or add your'
            ' local plugins by dropping them on the list below'
        )
        self._label.setWordWrap(True)
        self._label.setMargin(5)
        self.layout().addWidget(self._label)

        # plugin list
        self._plugin_list_widget = DndPluginList()
        self.layout().addWidget(self._plugin_list_widget)

        # apply and reset button.
        self._button_layout = QtWidgets.QHBoxLayout()

        self._apply_button = QtWidgets.QPushButton('Install Plugins')
        self._apply_button.setIcon(QtGui.QIcon(qta.icon('mdi6.check')))
        self._apply_button.setDisabled(True)

        self._reset_button = QtWidgets.QPushButton('Clear selection')
        self._reset_button.setIcon(QtGui.QIcon(qta.icon('mdi6.lock-reset')))
        self._reset_button.setMaximumWidth(120)

        self._button_layout.addWidget(self._apply_button)
        self._button_layout.addWidget(self._reset_button)

        self.layout().addLayout(self._button_layout)

        self._welcome_dialog = WelcomeDialog(self._on_restart_callback)
        self._welcome_dialog.hide()
        self.layout().addWidget(self._welcome_dialog)

        # overlays
        self._blocking_overlay = InstallerBlockingOverlay(self)
        self._blocking_overlay.hide()

        self._busy_overlay = BusyOverlay(self, 'Updating....')
        self._busy_overlay.hide()

    def post_build(self):
        # wire connections
        self._apply_button.clicked.connect(self._on_apply_changes)
        self._reset_button.clicked.connect(self._refresh)
        self._search_bar.textChanged.connect(
            self._plugin_list_widget.proxy_model.setFilterFixedString
        )
        self.show_welcome.connect(self._on_show_welcome_callback)
        self.apply_changes.connect(self.on_apply_changes_confirmed_callback)
        self.installation_started.connect(self._busy_overlay.show)
        self.installation_done.connect(self._busy_overlay.hide)
        self.installation_done.connect(self._show_user_message_done)
        self.installation_failed.connect(self._busy_overlay.hide)
        self.installation_failed.connect(self._show_user_message_failed)

        self.installation_done.connect(self._reset_overlay)
        self.installation_in_progress.connect(self._update_overlay)

        self.refresh_started.connect(self._busy_overlay.show)
        self.refresh_done.connect(self._busy_overlay.hide)

        self._plugin_list_widget.plugin_model.itemChanged.connect(
            self._enable_apply_button
        )

        self._blocking_overlay.confirm_button.clicked.connect(self._refresh)
        self._blocking_overlay.restart_button.clicked.connect(
            self._on_restart_callback
        )

    def _on_restart_callback(self):
        self.requestConnectRestart.emit()

    def _reset_plugin_list(self):
        self._counter = 0
        self._plugins_to_install = []

    def _emit_downloaded_plugins(self, plugins):
        metadata = []

        for plugin in plugins:
            name = str(plugin.data(ROLES.PLUGIN_NAME))
            version = str(plugin.data(ROLES.PLUGIN_VERSION))
            _os = str(platform.platform())

            plugin_data = {'name': name, 'version': version, 'os': _os}
            metadata.append(plugin_data)

        send_usage_event(
            self.session,
            'INSTALLED-CONNECT-PLUGINS',
            metadata,
            asynchronous=True,
        )

    def _enable_apply_button(self, item):
        '''Check the plugins state.'''
        self._apply_button.setDisabled(True)
        items = []
        for index in range(self._plugin_list_widget.plugin_model.rowCount()):
            if (
                self._plugin_list_widget.plugin_model.item(index).checkState()
                == QtCore.Qt.Checked
            ):
                items.append(self._plugin_list_widget.plugin_model.item(index))

        self._plugins_to_install = items

        if items:
            self._apply_button.setEnabled(True)

        self._apply_button.setText(
            f'Install {len(self._plugins_to_install)} Plugins'
        )

    @asynchronous
    def _refresh(self, on_init=False):
        '''Force refresh of the model, fetching all the available plugins.'''
        self.refresh_started.emit()
        installed_plugins_count = (
            self._plugin_list_widget.populate_installed_plugins()
        )
        self._plugin_list_widget.populate_download_plugins()
        self._enable_apply_button(None)
        self._reset_plugin_list()
        self.refresh_done.emit()
        if on_init and installed_plugins_count == 0:
            self.show_welcome.emit()

    def _on_show_welcome_callback(self):
        # Show dialog were user can choose to install all available plugins
        # Execute dialog and evaluate response
        self._label.setVisible(False)
        self._search_bar.setVisible(False)
        self._plugin_list_widget.setVisible(False)
        self._reset_button.setVisible(False)
        self._apply_button.setVisible(False)
        self._welcome_dialog.exec_()
        self._welcome_dialog.hide()
        self._label.setVisible(True)
        self._search_bar.setVisible(True)
        self._plugin_list_widget.setVisible(True)
        self._reset_button.setVisible(True)
        self._apply_button.setVisible(True)

    def _show_user_message_done(self):
        '''Show final message to the user.'''
        self._blocking_overlay.message = '<h2>Installation finished!</h2>'
        self._blocking_overlay.icon_data = qta.icon(
            'mdi6.check', color='#FFDD86', scale_factor=1.2
        )
        self._blocking_overlay.confirm_button.show()
        self._blocking_overlay.show()

    def _show_user_message_failed(self, reason):
        '''Show final message to the user.'''
        self._blocking_overlay.message = '<h2>Installation FAILED!</h2>'
        self._blocking_overlay.icon_data = qta.icon(
            'mdi6.close', color='#FF8686', scale_factor=1.2
        )
        self._blocking_overlay.set_reason(reason)
        self._blocking_overlay.confirm_button.show()
        self._blocking_overlay.show()

    def _reset_overlay(self):
        self._reset_plugin_list()
        self._busy_overlay.message = '<h2>Updating....</h2>'

    def _update_overlay(self, item):
        '''Update the overlay'''
        self._counter += 1

        self._busy_overlay.message = (
            f'<h2>Installing {self._counter} of {len(self._plugins_to_install)} plugins...</h2></br>'
            f'{item.data(ROLES.PLUGIN_NAME)}, Version {str(item.data(ROLES.PLUGIN_VERSION))}'
        )

    def _on_apply_changes(self):
        '''User wants to apply the updates, warn about conflicting plugins.'''
        conflicting_plugins = (
            self._plugin_list_widget.get_conflicting_plugins()
        )
        incompatible_plugins = (
            self._plugin_list_widget.get_incompatible_plugins()
        )
        deprecated_plugins = self._plugin_list_widget.get_deprecated_plugins()
        unloadable_plugins = conflicting_plugins + incompatible_plugins
        if unloadable_plugins:
            msgbox = QtWidgets.QMessageBox(
                QtWidgets.QMessageBox.Warning,
                'Warning',
                'The following conflicting and incompatible plugin(s) is installed and will be ignored by Connect'
                ':\n\n{}\n\nClean up and archive them?'.format(
                    '\n'.join(unloadable_plugins)
                ),
                buttons=QtWidgets.QMessageBox.Yes
                | QtWidgets.QMessageBox.No
                | QtWidgets.QMessageBox.Cancel,
                parent=self,
            )
            answer = msgbox.exec_()
            if answer == QtWidgets.QMessageBox.Yes:
                pass
            elif answer == QtWidgets.QMessageBox.No:
                unloadable_plugins = []  # Keep them
            elif answer == QtWidgets.QMessageBox.Cancel:
                return
        if deprecated_plugins:
            msgbox = QtWidgets.QMessageBox(
                QtWidgets.QMessageBox.Warning,
                'Warning',
                'The following deprecated plugin(s) is installed'
                ':\n\n{}\n\nClean up and archive them?\n\nNote: they might still function, please '
                'check release notes for further details.'.format(
                    '\n'.join(deprecated_plugins)
                ),
                buttons=QtWidgets.QMessageBox.Yes
                | QtWidgets.QMessageBox.No
                | QtWidgets.QMessageBox.Cancel,
                parent=self,
            )
            answer = msgbox.exec_()
            if answer == QtWidgets.QMessageBox.Yes:
                pass
            elif answer == QtWidgets.QMessageBox.No:
                deprecated_plugins = []  # Keep them
            else:
                return
        self.apply_changes.emit(unloadable_plugins + deprecated_plugins)

    @asynchronous
    def on_apply_changes_confirmed_callback(self, archive_plugins):
        '''Will process all the selected plugins.'''
        # Check if any conflicting plugins are installed.
        self.installation_started.emit()
        try:
            for plugin in archive_plugins:
                self._plugin_list_widget.archive_legacy_plugin(plugin)
            num_items = self._plugin_list_widget.plugin_model.rowCount()
            for i in range(num_items):
                item = self._plugin_list_widget.plugin_model.item(i)
                if item.checkState() == QtCore.Qt.Checked:
                    self.installation_in_progress.emit(item)
                    self._plugin_processor.process(item)
            self.installation_done.emit()
            self._emit_downloaded_plugins(self._plugins_to_install)
            self._reset_plugin_list()
        except:
            # Do not leave the overlay in a bad state.
            self.installation_failed.emit(traceback.format_exc())
