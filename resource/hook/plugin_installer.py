# :coding: utf-8
# :copyright: Copyright (c) 2014 ftrack

import os
import sys
import logging

cwd = os.path.dirname(__file__)
sources = os.path.abspath(os.path.join(cwd, '..', 'dependencies'))
sys.path.append(sources)

import ftrack_api
from Qt import QtWidgets, QtCore, QtGui
import qtawesome as qta

from ftrack_connect.ui.widget.overlay import BlockingOverlay, BusyOverlay
import ftrack_connect.ui.application
from ftrack_connect.asynchronous import asynchronous

from ftrack_connect_plugin_manager import (
    InstallerBlockingOverlay, PluginProcessor, DndPluginList, ROLES
)

logger = logging.getLogger('ftrack_connect.plugin.plugin_installer')


class PluginInstaller(ftrack_connect.ui.application.ConnectWidget):
    '''Show and manage plugin installations.'''

    name = 'Plugins'

    installation_done = QtCore.Signal()
    installation_started = QtCore.Signal()
    installation_in_progress = QtCore.Signal(object)

    refresh_started = QtCore.Signal()
    refresh_done = QtCore.Signal()

    # default methods
    def __init__(self, session, parent=None):
        '''Instantiate the actions widget.'''
        super(PluginInstaller, self).__init__(session, parent=parent)
        self.reset_plugin_list()

        self.plugin_processor = PluginProcessor()

        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)

        self.top_bar_layout = QtWidgets.QHBoxLayout()

        self.plugin_path_label = QtWidgets.QLabel()
        self.open_folder_button = QtWidgets.QPushButton('Open')
        self.open_folder_button.setIcon(QtGui.QIcon(qta.icon('mdi6.folder-home')))

        self.open_folder_button.setFixedWidth(150)

        self.top_bar_layout.addWidget(self.plugin_path_label)
        self.top_bar_layout.addWidget(self.open_folder_button)
        self.layout().addLayout(self.top_bar_layout)

        self.search_bar = QtWidgets.QLineEdit()
        self.search_bar.setPlaceholderText('Search plugin...')

        self.layout().addWidget(self.search_bar)

        # plugin list
        self.plugin_list_widget = DndPluginList(
            self.session
        )
        layout.addWidget(self.plugin_list_widget)

        self.plugin_path_label.setText('Using: <i>{}</i>'.format(
            self.plugin_list_widget.default_plugin_directory
        ))

        # apply and reset button.
        button_layout = QtWidgets.QHBoxLayout()

        self.apply_button = QtWidgets.QPushButton('Install Plugins')
        self.apply_button.setIcon(QtGui.QIcon(qta.icon('mdi6.check')))
        self.apply_button.setDisabled(True)

        self.reset_button = QtWidgets.QPushButton('Clear selection')
        self.reset_button.setIcon(QtGui.QIcon(qta.icon('mdi6.lock-reset')))
        self.reset_button.setMaximumWidth(100)

        button_layout.addWidget(self.apply_button)
        button_layout.addWidget(self.reset_button)

        layout.addLayout(button_layout)

        # overlays
        self.blockingOverlay = InstallerBlockingOverlay(self)
        self.blockingOverlay.hide()
        self.blockingOverlay.confirmButton.clicked.connect(self.refresh)

        self.busyOverlay = BusyOverlay(self, 'Updating....')
        self.busyOverlay.hide()

        # wire connections
        self.apply_button.clicked.connect(self._on_apply_changes)
        self.reset_button.clicked.connect(self.refresh)
        self.search_bar.textChanged.connect(self.plugin_list_widget.proxy_model.setFilterFixedString)
        self.open_folder_button.clicked.connect(self.openDefaultPluginDirectory)

        self.installation_started.connect(self.busyOverlay.show)
        self.installation_done.connect(self.busyOverlay.hide)
        self.installation_done.connect(self._show_user_message)
        self.installation_in_progress.connect(self._update_overlay)

        self.refresh_started.connect(self.busyOverlay.show)
        self.refresh_done.connect(self.busyOverlay.hide)

        self.plugin_list_widget.plugin_model.itemChanged.connect(self.enable_apply_button)

        # refresh
        self.refresh()

    def reset_plugin_list(self):
        self._plugins_to_install = []

    def emit_downloaded_plugins(self, plugins):
        metadata = []

        for plugin in plugins:
            name = plugin.data(ROLES.PLUGIN_NAME)
            version = plugin.data(ROLES.PLUGIN_VERSION)
            metadata.append({'name': name, 'version': version})

        ftrack_connect.usage.send_event(
            self.session,
            'INSTALLED-CONNECT-PLUGINS',
            metadata,
            asynchronous=False
        )

    def enable_apply_button(self, item):
        '''Check the plugins state.'''
        self.apply_button.setDisabled(True)
        items = []
        for index in range(self.plugin_list_widget.plugin_model.rowCount()):
            if self.plugin_list_widget.plugin_model.item(index).checkState() == QtCore.Qt.Checked:
                items.append(self.plugin_list_widget.plugin_model.item(index))

        self._plugins_to_install = items

        if items:
            self.apply_button.setEnabled(True)

        self.apply_button.setText(
            'Install {} Plugins'.format(
                len(self._plugins_to_install)
            )
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

    def _show_user_message(self):
        '''Show final message to the user.'''
        self.blockingOverlay.setMessage(
            'Installation finished!\n \n'
            'Please restart connect to pick up the changes.'
        )
        self.blockingOverlay.confirmButton.show()
        self.blockingOverlay.show()

    def _update_overlay(self, item):
        '''Update the overlay with the current item *information*.'''
        self.busyOverlay.setMessage(
            'Installing:\n\n{}\nVersion {} '.format(
                item.data(ROLES.PLUGIN_NAME),
                item.data(ROLES.PLUGIN_VERSION)
            )
        )

    @asynchronous
    def _on_apply_changes(self, event=None):
        '''Will process all the selected plugins.'''
        self.installation_started.emit()
        num_items = self.plugin_list_widget.plugin_model.rowCount()
        for i in range(num_items):
            item = self.plugin_list_widget.plugin_model.item(i)
            if item.checkState() == QtCore.Qt.Checked:
                self.installation_in_progress.emit(item)
                self.plugin_processor.process(item)
        self.installation_done.emit()
        self.emit_downloaded_plugins(self._plugins_to_install)
        self.reset_plugin_list()


    def openDefaultPluginDirectory(self):
        '''Open default plugin directory in platform default file browser.'''

        directory = self.plugin_list_widget.default_plugin_directory

        if not os.path.exists(directory):
            # Create directory if not existing.
            try:
                os.makedirs(directory)
            except OSError:
                messageBox = QtWidgets.QMessageBox(parent=self)
                messageBox.setIcon(QtWidgets.QMessageBox.Warning)
                messageBox.setText(
                    u'Could not open or create default plugin '
                    u'directory: {0}.'.format(directory)
                )
                messageBox.exec_()
                return

        ftrack_connect.util.open_directory(directory)


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
