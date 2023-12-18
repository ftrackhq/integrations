# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import os
import sys
import logging
import platform
import traceback
import qtawesome as qta

import ftrack_api

from ftrack_connect.qt import QtWidgets, QtCore, QtGui

from ftrack_connect.util import get_connect_plugin_version
from ftrack_connect.ui.widget.overlay import BlockingOverlay, BusyOverlay
import ftrack_connect.ui.application

from ftrack_connect.asynchronous import asynchronous

logger = logging.getLogger(__name__)

cwd = os.path.dirname(__file__)
connect_plugin_path = os.path.abspath(os.path.join(cwd, '..'))

# Read version number from __version__.py
__version__ = get_connect_plugin_version(connect_plugin_path)

python_dependencies = os.path.abspath(
    os.path.join(connect_plugin_path, 'dependencies')
)
sys.path.append(python_dependencies)

from ftrack_connect_plugin_manager import (
    InstallerBlockingOverlay,
    PluginProcessor,
    DndPluginList,
    ROLES,
)


class PluginInstaller(ftrack_connect.ui.application.ConnectWidget):
    '''Show and manage plugin installations.'''

    name = 'Plugins'

    installation_done = QtCore.Signal()
    installation_started = QtCore.Signal()
    installation_in_progress = QtCore.Signal(object)
    installation_failed = QtCore.Signal(object)

    refresh_started = QtCore.Signal()
    refresh_done = QtCore.Signal()

    apply_changes = QtCore.Signal(object)
    # List of conflicting plugins as argument

    # default methods
    def __init__(self, session, parent=None):
        '''Instantiate the plugin widget.'''
        super(PluginInstaller, self).__init__(session, parent=parent)

        self._search_bar = None
        self._plugin_list_widget = None
        self._apply_button = None
        self.reset_button = None
        self._blocking_overlay = None
        self._busy_overlay = None
        self._plugins_to_install = None
        self._counter = 0

        self.reset_plugin_list()
        self.plugin_processor = PluginProcessor()

        self.pre_build()
        self.build()
        self.post_build()

        # refresh
        self.refresh()

    def pre_build(self):
        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)

    def build(self):
        self._search_bar = QtWidgets.QLineEdit()
        self._search_bar.setPlaceholderText('Search plugin...')

        self.layout().addWidget(self._search_bar)
        label = QtWidgets.QLabel(
            'Check the plugins you want to install or add your'
            ' local plugins by dropping them on the list below'
        )
        label.setWordWrap(True)
        label.setMargin(5)
        self.layout().addWidget(label)

        # plugin list
        self._plugin_list_widget = DndPluginList()
        self.layout().addWidget(self._plugin_list_widget)

        # apply and reset button.
        button_layout = QtWidgets.QHBoxLayout()

        self._apply_button = QtWidgets.QPushButton('Install Plugins')
        self._apply_button.setIcon(QtGui.QIcon(qta.icon('mdi6.check')))
        self._apply_button.setDisabled(True)

        self.reset_button = QtWidgets.QPushButton('Clear selection')
        self.reset_button.setIcon(QtGui.QIcon(qta.icon('mdi6.lock-reset')))
        self.reset_button.setMaximumWidth(120)

        button_layout.addWidget(self._apply_button)
        button_layout.addWidget(self.reset_button)

        self.layout().addLayout(button_layout)

        # overlays
        self._blocking_overlay = InstallerBlockingOverlay(self)
        self._blocking_overlay.hide()

        self._busy_overlay = BusyOverlay(self, 'Updating....')
        self._busy_overlay.hide()

    def post_build(self):
        # wire connections
        self._apply_button.clicked.connect(self._on_apply_changes)
        self.reset_button.clicked.connect(self.refresh)
        self._search_bar.textChanged.connect(
            self._plugin_list_widget.proxy_model.setFilterFixedString
        )

        self.apply_changes.connect(self._on_apply_changes_confirmed)
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
            self.enable_apply_button
        )

        self._blocking_overlay.confirm_button.clicked.connect(self.refresh)
        self._blocking_overlay.restart_button.clicked.connect(
            self.requestConnectRestart.emit
        )

    def reset_plugin_list(self):
        self._counter = 0
        self._plugins_to_install = []

    def emit_downloaded_plugins(self, plugins):
        metadata = []

        for plugin in plugins:
            name = str(plugin.data(ROLES.PLUGIN_NAME))
            version = str(plugin.data(ROLES.PLUGIN_VERSION))
            _os = str(platform.platform())

            plugin_data = {'name': name, 'version': version, 'os': _os}
            metadata.append(plugin_data)

        ftrack_connect.usage.send_event(
            self.session,
            'INSTALLED-CONNECT-PLUGINS',
            metadata,
            asynchronous=True,
        )

    def enable_apply_button(self, item):
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
    def refresh(self):
        '''Force refresh of the model, fetching all the available plugins.'''
        self.refresh_started.emit()
        self._plugin_list_widget.populate_installed_plugins()
        self._plugin_list_widget.populate_download_plugins()
        self.enable_apply_button(None)
        self.reset_plugin_list()
        self.refresh_done.emit()

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
        self.reset_plugin_list()
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
        legacy_plugins = self._plugin_list_widget.get_legacy_plugins()
        if legacy_plugins:
            answer = QtWidgets.QMessageBox.question(
                None,
                'Warning',
                'The following deprecated plugin(s) is installed'
                ':\n\n{}\n\nRemove them?\n\nNote: they might still function, please '
                'check release notes for further details.'.format(
                    '\n'.join(legacy_plugins)
                ),
                QtWidgets.QMessageBox.Yes
                | QtWidgets.QMessageBox.No
                | QtWidgets.QMessageBox.Cancel,
            )
            if answer == QtWidgets.QMessageBox.Yes:
                pass
            elif answer == QtWidgets.QMessageBox.No:
                legacy_plugins = []
            else:
                return
        self.apply_changes.emit(legacy_plugins)

    @asynchronous
    def _on_apply_changes_confirmed(self, legacy_plugins):
        '''Will process all the selected plugins.'''
        # Check if any conflicting plugins are installed.
        self.installation_started.emit()
        try:
            for plugin in legacy_plugins:
                self._plugin_list_widget.remove_legacy_plugin(plugin)
            num_items = self._plugin_list_widget.plugin_model.rowCount()
            for i in range(num_items):
                item = self._plugin_list_widget.plugin_model.item(i)
                if item.checkState() == QtCore.Qt.Checked:
                    self.installation_in_progress.emit(item)
                    self.plugin_processor.process(item)
            self.installation_done.emit()
            self.emit_downloaded_plugins(self._plugins_to_install)
            self.reset_plugin_list()
        except:
            # Do not leave the overlay in a bad state.
            self.installation_failed.emit(traceback.format_exc())


def get_version_information(event):
    '''Return version information for ftrack connect plugin.'''
    return [dict(name='connect-plugin-manager', version=__version__)]


def register(session, **kw):
    '''Register plugin. Called when used as a plugin.'''
    # Validate that session is an instance of ftrack_api.Session. If not,
    # assume that register is being called from an old or incompatible API and
    # return without doing anything.
    if not isinstance(session, ftrack_api.session.Session):
        logger.debug(
            'Not subscribing plugin as passed argument {0!r} is not an '
            'ftrack_api.Session instance.'.format(session)
        )
        return

    #  Uncomment to register plugin
    plugin = ftrack_connect.ui.application.ConnectWidgetPlugin(PluginInstaller)
    plugin.register(session, priority=30)

    # Enable plugin info in Connect about dialog
    session.event_hub.subscribe(
        'topic=ftrack.connect.plugin.debug-information',
        get_version_information,
        priority=20,
    )
