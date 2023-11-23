# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import os
import sys
import logging
import platform
import traceback

from functools import partial

from ftrack_connect.qt import QtWidgets, QtCore, QtGui


import qtawesome as qta

import ftrack_api

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
    InstallerDoneBlockingOverlay,
    InstallerFailedBlockingOverlay,
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

    apply_changes = QtCore.Signal()

    # default methods
    def __init__(self, session, parent=None):
        '''Instantiate the actions widget.'''
        super(PluginInstaller, self).__init__(session, parent=parent)
        self.reset_plugin_list()

        self.plugin_processor = PluginProcessor()

        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)

        self.search_bar = QtWidgets.QLineEdit()
        self.search_bar.setPlaceholderText('Search plugin...')

        self.layout().addWidget(self.search_bar)
        label = QtWidgets.QLabel(
            'Check the plugins you want to install or add your'
            ' local plugins by dropping them on the list below'
        )
        label.setWordWrap(True)
        label.setMargin(5)
        self.layout().addWidget(label)

        # plugin list
        self.plugin_list_widget = DndPluginList(self.session)
        layout.addWidget(self.plugin_list_widget)

        # apply and reset button.
        button_layout = QtWidgets.QHBoxLayout()

        self.apply_button = QtWidgets.QPushButton('Install Plugins')
        self.apply_button.setIcon(QtGui.QIcon(qta.icon('mdi6.check')))
        self.apply_button.setDisabled(True)

        self.reset_button = QtWidgets.QPushButton('Clear selection')
        self.reset_button.setIcon(QtGui.QIcon(qta.icon('mdi6.lock-reset')))
        self.reset_button.setMaximumWidth(120)

        button_layout.addWidget(self.apply_button)
        button_layout.addWidget(self.reset_button)

        layout.addLayout(button_layout)

        # overlays
        self.blockingOverlayDone = InstallerDoneBlockingOverlay(self)
        self.blockingOverlayDone.hide()
        self.blockingOverlayDone.confirmButton.clicked.connect(self.refresh)
        self.blockingOverlayDone.restartButton.clicked.connect(
            self.requestConnectRestart.emit
        )

        self.blockingOverlayFailed = InstallerFailedBlockingOverlay(self)
        self.blockingOverlayFailed.hide()
        self.blockingOverlayFailed.confirmButton.clicked.connect(self.refresh)
        self.blockingOverlayFailed.restartButton.clicked.connect(
            self.requestConnectRestart.emit
        )

        self.busyOverlay = BusyOverlay(self, 'Updating....')
        self.busyOverlay.hide()

        # wire connections
        self.apply_button.clicked.connect(self._on_apply_changes)
        self.reset_button.clicked.connect(self.refresh)
        self.search_bar.textChanged.connect(
            self.plugin_list_widget.proxy_model.setFilterFixedString
        )

        self.apply_changes.connect(self._on_apply_changes_confirmed)
        self.installation_started.connect(self.busyOverlay.show)
        self.installation_done.connect(self.busyOverlay.hide)
        self.installation_done.connect(
            partial(self._show_user_message_done, 'Installation finished!')
        )
        self.installation_failed.connect(self.busyOverlay.hide)
        self.installation_failed.connect(
            partial(self._show_user_message_failed, 'Installation FAILED!')
        )

        self.installation_done.connect(self._reset_overlay)
        self.installation_in_progress.connect(self._update_overlay)

        self.refresh_started.connect(self.busyOverlay.show)
        self.refresh_done.connect(self.busyOverlay.hide)

        self.plugin_list_widget.plugin_model.itemChanged.connect(
            self.enable_apply_button
        )

        # refresh
        self.refresh()

    def reset_plugin_list(self):
        self.counter = 0
        self._plugins_to_install = []

    def emit_downloaded_plugins(self, plugins):
        metadata = []

        for plugin in plugins:
            name = str(plugin.data(ROLES.PLUGIN_NAME))
            version = str(plugin.data(ROLES.PLUGIN_VERSION))
            os = str(platform.platform())

            plugin_data = {'name': name, 'version': version, 'os': os}
            metadata.append(plugin_data)

        ftrack_connect.usage.send_event(
            self.session,
            'INSTALLED-CONNECT-PLUGINS',
            metadata,
            asynchronous=True,
        )

    def enable_apply_button(self, item):
        '''Check the plugins state.'''
        self.apply_button.setDisabled(True)
        items = []
        for index in range(self.plugin_list_widget.plugin_model.rowCount()):
            if (
                self.plugin_list_widget.plugin_model.item(index).checkState()
                == QtCore.Qt.Checked
            ):
                items.append(self.plugin_list_widget.plugin_model.item(index))

        self._plugins_to_install = items

        if items:
            self.apply_button.setEnabled(True)

        self.apply_button.setText(
            'Install {} Plugins'.format(len(self._plugins_to_install))
        )

    @asynchronous
    def refresh(self):
        '''Force refresh of the model, fetching all the available plugins.'''
        self.refresh_started.emit()
        self.plugin_list_widget.populate_installed_plugins()
        self.plugin_list_widget.populate_download_plugins()
        self.enable_apply_button(None)
        self.reset_plugin_list()
        self.refresh_done.emit()

    def _show_user_message_done(self, message):
        '''Show final message to the user.'''
        self.blockingOverlayDone.setMessage('<h2>{}</h2>'.format(message))
        self.blockingOverlayDone.confirmButton.show()
        self.blockingOverlayDone.show()

    def _show_user_message_failed(self, message, reason):
        '''Show final message to the user.'''
        self.blockingOverlayFailed.setMessage('<h2>{}</h2>'.format(message))
        self.blockingOverlayFailed.setReason(reason)
        self.blockingOverlayFailed.confirmButton.show()
        self.blockingOverlayFailed.show()

    def _reset_overlay(self):
        self.reset_plugin_list()
        self.busyOverlay.setMessage('<h2>Updating....</h2>')

    def _update_overlay(self, item):
        '''Update the overlay with the current item *information*.'''
        self.counter += 1

        self.busyOverlay.setMessage(
            '<h2>Installing {} of {} plugins...</h2></br>'
            '{}, Version {}'.format(
                self.counter,
                len(self._plugins_to_install),
                item.data(ROLES.PLUGIN_NAME),
                str(item.data(ROLES.PLUGIN_VERSION)),
            )
        )

    def _on_apply_changes(self, event=None):
        conflicting_plugins = self.plugin_list_widget.get_conflicting_plugins()
        if conflicting_plugins:
            if (
                QtWidgets.QMessageBox.question(
                    None,
                    "Warning",
                    "The following conflicting/deprecated"
                    " plugins will be removed:\n\n{}\n\nProceed?".format(
                        "\n".join(conflicting_plugins)
                    ),
                )
                == QtWidgets.QMessageBox.No
            ):
                return
        self.apply_changes.emit()

    @asynchronous
    def _on_apply_changes_confirmed(self, event=None):
        '''Will process all the selected plugins.'''
        # Check if any conflicting plugins are installed.
        self.installation_started.emit()
        try:
            conflicting_plugins = (
                self.plugin_list_widget.get_conflicting_plugins()
            )
            for plugin in conflicting_plugins:
                self.plugin_list_widget.remove_conflicting_plugin(plugin)
            num_items = self.plugin_list_widget.plugin_model.rowCount()
            for i in range(num_items):
                item = self.plugin_list_widget.plugin_model.item(i)
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
    '''Register plugin. Called when used as an plugin.'''
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
