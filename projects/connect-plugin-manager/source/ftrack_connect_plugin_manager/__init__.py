# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import os
import re
import logging
import shutil
import traceback
import zipfile
import tempfile
import urllib
from urllib.request import urlopen
from urllib.error import HTTPError
from packaging.version import parse as parse_version
import appdirs
import json
import sys

from ftrack_connect.qt import QtWidgets, QtCore, QtGui
import qtawesome as qta

from ftrack_connect.ui.widget.overlay import BlockingOverlay

logger = logging.getLogger(__name__)

# Evaluate version and log package version
try:
    from ftrack_utils.version import get_version

    __version__ = get_version(
        os.path.basename(os.path.dirname(__file__)),
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    )
except Exception:
    __version__ = '0.0.0'


class InstallerBlockingOverlay(BlockingOverlay):
    '''Custom blocking overlay for plugin installer.'''

    def __init__(
        self,
        parent,
        message='',
        icon=qta.icon('mdi6.check', color='#FFDD86', scale_factor=1.2),
    ):
        super(InstallerBlockingOverlay, self).__init__(
            parent,
            message=message,
            icon=icon,
        )

        self._text_edit = QtWidgets.QTextEdit()
        self._text_edit.setReadOnly(True)
        self._text_edit.setFixedHeight(200)
        self.contentLayout.addWidget(self._text_edit)
        self._text_edit.setVisible(False)

        self._button_layout = QtWidgets.QHBoxLayout()
        self._button_layout.setContentsMargins(0, 0, 0, 0)
        self.contentLayout.addSpacing(30)
        self.contentLayout.addLayout(self._button_layout)
        self.confirm_button = QtWidgets.QPushButton('Install more plugins')
        self.restart_button = QtWidgets.QPushButton('Restart')
        self.restart_button.setObjectName('primary')

        self._button_layout.addWidget(self.confirm_button)
        self._button_layout.addWidget(self.restart_button)
        self.confirm_button.hide()
        self.confirm_button.clicked.connect(self.hide)

    def set_reason(self, reason):
        self._text_edit.setText(reason)
        self._text_edit.setVisible(True)


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
    STATUSES.NEW: QtGui.QIcon(qta.icon('mdi6.new-box')),
    STATUSES.UPDATE: QtGui.QIcon(qta.icon('mdi6.update')),
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
            STATUSES.DOWNLOAD: self.install,
        }

    def download(self, plugin):
        '''Download provided *plugin* item.'''
        source_path_noarch = plugin.data(ROLES.PLUGIN_SOURCE_PATH)
        # Determine our platform
        if sys.platform.startswith('win'):
            platform = 'win'
        elif sys.platform.startswith('linux'):
            platform = 'linux'
        elif sys.platform.startswith('darwin'):
            platform = 'mac'
        else:
            platform = sys.platform

        for platform_dependent, source_path in [
            (
                True,
                source_path_noarch.replace('.zip', f'-{platform}.zip'),
            ),
            (False, source_path_noarch),
        ]:
            try:
                zip_name = os.path.basename(source_path_noarch)
                save_path = tempfile.gettempdir()
                temp_path = os.path.join(save_path, zip_name)

                logger.info(f'Downloading {source_path} to {temp_path}')

                with urllib.request.urlopen(source_path) as dl_file:
                    with open(temp_path, 'wb') as out_file:
                        out_file.write(dl_file.read())
                return temp_path
            except HTTPError as e:
                if platform_dependent:
                    logger.debug(
                        f'No download exists {source_path} on platform {platform}'
                    )
                else:
                    logger.warning(traceback.format_exc())
                    raise Exception(
                        f'Plugin "{plugin.data(ROLES.PLUGIN_NAME)}" is not supported on this platform'
                        f' or temporarily unavailable. Details: {e}'
                    )

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
        logger.debug(f'Installing {source_path} to {destination_path}')

        with zipfile.ZipFile(source_path, 'r') as zip_ref:
            zip_ref.extractall(destination_path)

    def remove(self, plugin):
        '''Remove provided *plugin* item.'''
        install_path = plugin.data(ROLES.PLUGIN_INSTALL_PATH)
        logger.debug(f'Removing {install_path}')
        if os.path.exists(install_path) and os.path.isdir(install_path):
            shutil.rmtree(install_path, ignore_errors=False, onerror=None)


class DndPluginList(QtWidgets.QFrame):
    '''Plugin list widget'''

    default_json_config_url = (
        'https://download.ftrack.com/ftrack-connect/plugins.json'
    )

    plugin_re = re.compile('(?P<name>(([A-Za-z-3-4]+)))-(?P<version>(\w.+))')

    @property
    def proxy_model(self):
        '''Return proxy model.'''
        return self._proxy_model

    @property
    def plugin_model(self):
        '''Return plugin model.'''
        return self._plugin_model

    def __init__(self, parent=None):
        super(DndPluginList, self).__init__(parent=parent)

        self.json_config_url = os.environ.get(
            'FTRACK_CONNECT_JSON_PLUGINS_URL', self.default_json_config_url
        )

        self.default_plugin_directory = appdirs.user_data_dir(
            'ftrack-connect-plugins', 'ftrack'
        )

        self._plugin_list = None
        self._plugin_model = None
        self._proxy_model = None

        self.setAcceptDrops(True)

        self.pre_build()
        self.build()
        self.post_build()

    def pre_build(self):
        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

    def build(self):
        self._plugin_list = QtWidgets.QListView()
        self._plugin_model = QtGui.QStandardItemModel(self)
        self._proxy_model = QtCore.QSortFilterProxyModel(self)
        self._proxy_model.setSourceModel(self._plugin_model)
        self._plugin_list.setModel(self._proxy_model)
        self.layout().addWidget(self._plugin_list)

    def post_build(self):
        pass

    # custom methods
    def add_plugin(self, file_path, status=STATUSES.NEW):
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

        plugin_item.setText(f'{data["name"]} | {data["version"]}')
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
                plugin_item.setData(file_path, ROLES.PLUGIN_INSTALL_PATH)
                plugin_item.setEnabled(False)
                plugin_item.setCheckable(False)

            elif status in [STATUSES.NEW, STATUSES.DOWNLOAD]:
                destination_path = os.path.join(
                    self.default_plugin_directory, os.path.basename(file_path)
                )

                plugin_item.setData(
                    destination_path, ROLES.PLUGIN_INSTALL_PATH
                )

                plugin_item.setData(file_path, ROLES.PLUGIN_SOURCE_PATH)

                if status is STATUSES.NEW:
                    # enable it by default as is new.
                    plugin_item.setCheckable(True)
                    plugin_item.setCheckState(QtCore.Qt.Checked)

            self._plugin_model.appendRow(plugin_item)
            self._plugin_model.itemChanged.emit(plugin_item)
            return

        # update/remove plugin
        stored_status = stored_item.data(ROLES.PLUGIN_STATUS)
        if stored_status in [
            STATUSES.INSTALLED,
            STATUSES.DOWNLOAD,
        ] and status in [STATUSES.NEW, STATUSES.DOWNLOAD]:
            stored_plugin_version = stored_item.data(ROLES.PLUGIN_VERSION)
            should_update = stored_plugin_version < new_plugin_version
            if not should_update:
                return

            # update stored item.
            stored_item.setText(f'{stored_item.text()} > {new_plugin_version}')
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
        num_items = self._plugin_model.rowCount()
        for i in range(num_items):
            item = self._plugin_model.item(i)
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
        self._plugin_model.clear()

        plugins = os.listdir(self.default_plugin_directory)

        for plugin in plugins:
            plugin_path = os.path.join(self.default_plugin_directory, plugin)
            self.add_plugin(plugin_path, STATUSES.INSTALLED)

    def populate_download_plugins(self):
        '''Populate model with remotely configured plugins.'''

        response = urlopen(self.json_config_url)
        response_json = json.loads(response.read())

        for link in response_json['integrations']:
            self.add_plugin(link, STATUSES.DOWNLOAD)

    def get_legacy_plugins(self):
        result = []
        plugins = os.listdir(self.default_plugin_directory)
        for plugin in plugins:
            if (
                plugin.lower().startswith('ftrack-connect-pipeline')
                or plugin.lower().find('ftrack-application-launcher') > -1
            ):
                result.append(plugin)
        return result

    def remove_legacy_plugin(self, plugin_name):
        install_path = os.path.join(self.default_plugin_directory, plugin_name)
        logger.debug(f'Removing legacy plugin: {install_path}')
        if os.path.exists(install_path) and os.path.isdir(install_path):
            shutil.rmtree(install_path, ignore_errors=False, onerror=None)

    def _process_mime_data(self, mime_data):
        '''Return a list of valid filepaths.'''
        validPaths = []

        if not mime_data.hasUrls():
            QtWidgets.QMessageBox.warning(
                self,
                'Invalid file',
                'Invalid file: the dropped item is not a valid file.',
            )
            return validPaths

        for path in mime_data.urls():
            local_path = path.toLocalFile()
            if os.path.isfile(local_path):
                if local_path.endswith('.zip'):
                    validPaths.append(local_path)

        return validPaths

    def dragEnterEvent(self, event):
        '''Override dragEnterEvent and accept all events.'''
        event.setDropAction(QtCore.Qt.CopyAction)
        event.accept()
        self._set_drop_zone_state('active')

    def dropEvent(self, event):
        '''Handle dropped file event.'''
        self._set_drop_zone_state()

        paths = self._process_mime_data(event.mimeData())

        for path in paths:
            self.add_plugin(path, STATUSES.NEW)

        event.accept()
        self._set_drop_zone_state()

    def _set_drop_zone_state(self, state='default'):
        '''Set drop zone state to *state*.

        *state* should be 'default', 'active' or 'invalid'.

        '''
        self.setProperty('ftrackDropZoneState', state)
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()
