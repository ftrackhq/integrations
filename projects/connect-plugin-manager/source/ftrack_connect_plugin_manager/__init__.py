# :coding: utf-8
# :copyright: Copyright (c) 2014 ftrack
import os
import re
import logging
import shutil
import zipfile
import tempfile
import urllib
from urllib.request import urlopen
from packaging.version import parse as parse_version
import appdirs
import json

from ftrack_connect.qt import QtWidgets, QtCore, QtGui
import qtawesome as qta

from ftrack_connect.ui.widget.overlay import BlockingOverlay


class InstallerBlockingOverlay(
    BlockingOverlay
):
    '''Custom blocking overlay for publisher.'''

    def __init__(self, parent, message=''):
        super(InstallerBlockingOverlay, self).__init__(
            parent, message=message, icon=qta.icon('mdi6.check', color='#FFDD86', scale_factor=1.2)
        )

        self.button_layout = QtWidgets.QHBoxLayout()
        self.button_layout.setContentsMargins(0, 0, 0, 0)
        self.contentLayout.addSpacing(30)
        self.contentLayout.addLayout(self.button_layout)
        self.confirmButton = QtWidgets.QPushButton('Install more plugins')
        self.restartButton = QtWidgets.QPushButton('Restart')
        self.restartButton.setObjectName('primary')

        self.button_layout.addWidget(
            self.confirmButton
        )
        self.button_layout.addWidget(
            self.restartButton
        )
        self.confirmButton.hide()
        self.confirmButton.clicked.connect(self.hide)


class STATUSES(object):
    '''Store plugin statuses'''
    INSTALLED = 0
    NEW = 1
    UPDATE = 2
    REMOVE = 3
    DOWNLOAD = 4


class ROLES(object):
    '''Store plugin roles'''

    PLUGIN_STATUS = QtCore.Qt.UserRole + 1
    PLUGIN_NAME = PLUGIN_STATUS + 1
    PLUGIN_VERSION = PLUGIN_NAME + 1
    PLUGIN_SOURCE_PATH = PLUGIN_VERSION + 1
    PLUGIN_INSTALL_PATH = PLUGIN_SOURCE_PATH + 1
    PLUGIN_ID = PLUGIN_INSTALL_PATH + 1


# Icon representation for statuses
STATUS_ICONS = {
    STATUSES.INSTALLED: QtGui.QIcon(qta.icon('mdi6.harddisk')),
    STATUSES.NEW:  QtGui.QIcon(qta.icon('mdi6.new-box')),
    STATUSES.UPDATE:  QtGui.QIcon(qta.icon('mdi6.update')),
    STATUSES.DOWNLOAD: QtGui.QIcon(qta.icon('mdi6.download')),

}


class PluginProcessor(QtCore.QObject):
    '''Handles installation process of plugins.'''

    def __init__(self):
        super(PluginProcessor, self).__init__()

        self.process_mapping = {
            STATUSES.NEW: self.install,
            STATUSES.UPDATE: self.update,
            STATUSES.REMOVE: self.remove,
            STATUSES.DOWNLOAD: self.install
        }

    def download(self, plugin):
        '''Download provided *plugin* item.'''
        source_path = plugin.data(ROLES.PLUGIN_SOURCE_PATH)
        zip_name = os.path.basename(source_path)
        save_path = tempfile.gettempdir()
        temp_path = os.path.join(save_path, zip_name)
        logging.debug('Downloading {} to {}'.format(source_path, temp_path))

        with urllib.request.urlopen(source_path) as dl_file:
            with open(temp_path, 'wb') as out_file:
                out_file.write(dl_file.read())
        return temp_path

    def process(self, plugin):
        '''Process provided *plugin* item.'''

        status = plugin.data(ROLES.PLUGIN_STATUS)
        plugin_fn = self.process_mapping.get(status)

        if not plugin_fn:
            return

        plugin_fn(plugin)

    def update(self, plugin):
        '''Update provided *plugin* item.'''
        self.remove(plugin)
        self.install(plugin)

    def install(self, plugin):
        '''Install provided *plugin* item.'''
        source_path = plugin.data(ROLES.PLUGIN_SOURCE_PATH)
        if source_path.startswith('http'):
            source_path = self.download(plugin)

        plugin_name = os.path.basename(source_path).split('.zip')[0]

        install_path = os.path.dirname(plugin.data(ROLES.PLUGIN_INSTALL_PATH))
        destination_path = os.path.join(install_path, plugin_name)
        logging.debug('Installing {} to {}'.format(source_path, destination_path))

        with zipfile.ZipFile(source_path, 'r') as zip_ref:
            zip_ref.extractall(destination_path)

    def remove(self, plugin):
        '''Remove provided *plugin* item.'''
        install_path = plugin.data(ROLES.PLUGIN_INSTALL_PATH)
        logging.debug('Removing {}'.format(install_path))
        if os.path.exists(install_path) and os.path.isdir(install_path):
            shutil.rmtree(install_path, ignore_errors=False, onerror=None)


class DndPluginList(QtWidgets.QFrame):

    default_json_config_url = 'https://download.ftrack.com/ftrack-connect/plugins.json'
    plugin_re = re.compile(
        '(?P<name>(([A-Za-z-3-4]+)))-(?P<version>(\w.+))'
    )

    def __init__(self, session, parent=None):
        super(DndPluginList, self).__init__(parent=parent)

        self.json_config_url = os.environ.get(
            'FTRACK_CONNECT_JSON_PLUGINS_URL',
            self.default_json_config_url
        )

        self.default_plugin_directory = appdirs.user_data_dir(
            'ftrack-connect-plugins', 'ftrack'
        )

        self.setAcceptDrops(True)

        self.main_layout = QtWidgets.QVBoxLayout()
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.main_layout)
        self.plugin_list = QtWidgets.QListView()
        self.plugin_model = QtGui.QStandardItemModel(self)
        self.proxy_model = QtCore.QSortFilterProxyModel(self)
        self.proxy_model.setSourceModel(self.plugin_model)
        self.plugin_list.setModel(self.proxy_model)
        self.main_layout.addWidget(self.plugin_list)

    # custom methods
    def addPlugin(self, file_path, status=STATUSES.NEW):
        '''Add provided *plugin_path* as plugin with given *status*.'''
        if not file_path:
            return

        data = self._is_plugin_valid(file_path)

        if not data:
            return

        # create new plugin item and populate it with data
        plugin_id = str(hash(data['name']))
        data['id'] = plugin_id

        plugin_item = QtGui.QStandardItem()

        plugin_item.setCheckable(True)
        plugin_item.setEditable(False)
        plugin_item.setSelectable(False)
        plugin_item.setEnabled(True)

        plugin_item.setText('{} | {}'.format(data['name'], data['version']))
        plugin_item.setData(status, ROLES.PLUGIN_STATUS)
        plugin_item.setData(str(data['name']), ROLES.PLUGIN_NAME)
        new_plugin_version = parse_version(data['version'])
        plugin_item.setData(new_plugin_version, ROLES.PLUGIN_VERSION)
        plugin_item.setData(plugin_id, ROLES.PLUGIN_ID)
        plugin_item.setIcon(STATUS_ICONS[status])

        # check if is a new plugin.....
        stored_item = self.plugin_is_available(data)

        if not stored_item:
            # add new plugin
            if status == STATUSES.INSTALLED:
                plugin_item.setData(
                    file_path, ROLES.PLUGIN_INSTALL_PATH
                )
                plugin_item.setEnabled(False)
                plugin_item.setCheckable(False)

            elif status in [STATUSES.NEW, STATUSES.DOWNLOAD]:
                destination_path = os.path.join(
                    self.default_plugin_directory,
                    os.path.basename(file_path)
                )

                plugin_item.setData(
                    destination_path, ROLES.PLUGIN_INSTALL_PATH
                )

                plugin_item.setData(
                    file_path, ROLES.PLUGIN_SOURCE_PATH
                )

                if status is STATUSES.NEW:
                    # enable it by default as is new.
                    plugin_item.setCheckable(True)
                    plugin_item.setCheckState(QtCore.Qt.Checked)

            self.plugin_model.appendRow(plugin_item)
            self.plugin_model.itemChanged.emit(plugin_item)
            return

        # update/remove plugin
        stored_status = stored_item.data(ROLES.PLUGIN_STATUS)
        if (
                stored_status in [STATUSES.INSTALLED, STATUSES.DOWNLOAD] and
                status in [STATUSES.NEW, STATUSES.DOWNLOAD]
        ):
            stored_plugin_version = stored_item.data(ROLES.PLUGIN_VERSION)
            should_update = stored_plugin_version < new_plugin_version
            if not should_update:
                return

            # update stored item.
            stored_item.setText(
                '{} > {}'.format(stored_item.text(), new_plugin_version)
            )
            stored_item.setData(STATUSES.UPDATE, ROLES.PLUGIN_STATUS)
            stored_item.setIcon(STATUS_ICONS[STATUSES.UPDATE])
            stored_item.setData(file_path, ROLES.PLUGIN_SOURCE_PATH)
            stored_item.setData(new_plugin_version, ROLES.PLUGIN_VERSION)

            # enable it by default if we are updating
            stored_item.setCheckable(True)
            stored_item.setEnabled(True)
            stored_item.setCheckState(QtCore.Qt.Checked)

    def plugin_is_available(self, plugin_data):
        '''Return item from *plugin_data* if found.'''
        num_items = self.plugin_model.rowCount()
        for i in range(num_items):
            item = self.plugin_model.item(i)
            item_id = item.data(ROLES.PLUGIN_ID)
            if item_id == plugin_data['id']:
                return item
        return None

    def _is_plugin_valid(self, plugin_path):
        '''Return whether the provided *plugin_path* is a valid plugin.'''
        plugin_name = os.path.basename(plugin_path)
        match = self.plugin_re.match(plugin_name)
        if match:
            data = match.groupdict()
        else:
            return False

        if data['version'].endswith('.zip'):
            # pop zip extension from the version.
            # TODO: refine regex to catch extension
            data['version'] = data['version'][:-4]
        return data

    def populate_installed_plugins(self):
        '''Populate model with installed plugins.'''
        self.plugin_model.clear()

        plugins = os.listdir(
            self.default_plugin_directory
        )

        for plugin in plugins:
            plugin_path = os.path.join(
                self.default_plugin_directory,
                plugin
            )
            self.addPlugin(plugin_path, STATUSES.INSTALLED)

    def populate_download_plugins(self):
        '''Populate model with remotely configured plugins.'''

        response = urlopen(self.json_config_url)
        response_json = json.loads(response.read())

        for link in response_json['integrations']:
            self.addPlugin(link, STATUSES.DOWNLOAD)

    def _processMimeData(self, mimeData):
        '''Return a list of valid filepaths.'''
        validPaths = []

        if not mimeData.hasUrls():
            QtWidgets.QMessageBox.warning(
                self,
                'Invalid file',
                'Invalid file: the dropped item is not a valid file.'
            )
            return validPaths

        for path in mimeData.urls():
            local_path = path.toLocalFile()
            if os.path.isfile(local_path):
                if local_path.endswith('.zip'):
                    validPaths.append(local_path)

        return validPaths

    def dragEnterEvent(self, event):
        '''Override dragEnterEvent and accept all events.'''
        event.setDropAction(QtCore.Qt.CopyAction)
        event.accept()
        self._setDropZoneState('active')

    def dropEvent(self, event):
        '''Handle dropped file event.'''
        self._setDropZoneState()

        paths = self._processMimeData(
            event.mimeData()
        )

        for path in paths:
            self.addPlugin(path, STATUSES.NEW)

        event.accept()
        self._setDropZoneState()


    def _setDropZoneState(self, state='default'):
        '''Set drop zone state to *state*.

        *state* should be 'default', 'active' or 'invalid'.

        '''
        self.setProperty('ftrackDropZoneState', state)
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()