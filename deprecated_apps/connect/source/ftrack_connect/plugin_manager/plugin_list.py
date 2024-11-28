# :coding: utf-8
# :copyright: Copyright (c) 2014-2024 ftrack
import re
import os
import platformdirs
from packaging.version import parse as parse_version
from urllib.request import urlopen
import json
import shutil
import logging
import qtawesome as qta

from ftrack_connect import DEFAULT_INTEGRATIONS_REPO_URL

try:
    from PySide6 import QtWidgets, QtCore, QtGui
except ImportError:
    from PySide2 import QtWidgets, QtCore, QtGui

from ftrack_connect.utils.plugin import (
    PLUGIN_DIRECTORIES,
    get_plugin_json_url_from_environment,
    fetch_github_releases,
    get_plugin_data,
    get_platform_identifier,
)
from ftrack_connect.utils.thread import qt_main_thread

from ftrack_connect.plugin_manager.processor import (
    STATUSES,
    ROLES,
    STATUS_ICONS,
)


logger = logging.getLogger(__name__)


class DndPluginList(QtWidgets.QFrame):
    '''Plugin list widget'''

    @property
    def proxy_model(self):
        '''Return proxy model.'''
        return self._proxy_model

    @property
    def plugin_model(self):
        '''Return plugin model.'''
        return self._plugin_model

    @property
    def installed_plugins(self):
        '''Return installed plugin count.'''
        return self._installed_plugins

    @property
    def downloadable_plugin_count(self):
        '''Return downloadable plugin count.'''
        return self._downloadable_plugin_count

    def __init__(self, parent=None):
        super(DndPluginList, self).__init__(parent=parent)

        # Set the plugin directory to install to the first path on PLUGIN_DIRECTORIES
        self.default_install_plugin_directory = PLUGIN_DIRECTORIES[0]

        # If set, download plugins from this url instead of the releases
        self._json_config_url = get_plugin_json_url_from_environment()

        self._installed_plugins = []
        self._plugin_list = None
        self._plugin_model = None
        self._proxy_model = None
        self._installed_plugin_count = 0
        self._downloadable_plugin_count = 0

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
    @qt_main_thread
    def _add_plugin(self, plugin_data, status=STATUSES.NEW):
        '''Add provided *plugin_data* as plugin with given *status*.'''

        if not plugin_data:
            return

        # Check platform
        platform = get_platform_identifier()
        destination_filename = os.path.basename(plugin_data['path'])
        if destination_filename.lower().endswith('.zip'):
            destination_filename = destination_filename[:-4]
        if plugin_data['platform'] != 'noarch':
            if plugin_data['platform'] != platform:
                # Not our platform, ask user if they want to install anyway
                msgbox = QtWidgets.QMessageBox(
                    QtWidgets.QMessageBox.Icon.Warning,
                    'Warning',
                    'This plugin is not compatible with your platform:'
                    f':\n\n{destination_filename}\n\nProceed install anyway?',
                    buttons=QtWidgets.QMessageBox.StandardButton.Yes
                    | QtWidgets.QMessageBox.StandardButton.No
                    | QtWidgets.QMessageBox.StandardButton.Cancel,
                    parent=self,
                )
                answer = msgbox.exec_()
                if answer == QtWidgets.QMessageBox.StandardButton.Yes:
                    pass
                elif answer == QtWidgets.QMessageBox.StandardButton.No:
                    return  # Skip this one, but proceed
                elif answer == QtWidgets.QMessageBox.StandardButton.Cancel:
                    raise Exception('Plugin installation cancelled by user.')

            if destination_filename.endswith(f'-{plugin_data["platform"]}'):
                destination_filename = destination_filename[
                    : -len(plugin_data["platform"]) - 1
                ]

        # create new plugin item and populate it with data
        plugin_id = str(hash(plugin_data['name']))
        plugin_data['id'] = plugin_id

        plugin_item = QtGui.QStandardItem()

        plugin_item.setCheckable(True)
        plugin_item.setEditable(False)
        plugin_item.setSelectable(False)
        plugin_item.setEnabled(True)

        plugin_item.setText(
            f'{plugin_data["name"]} | {plugin_data["version"]}'
        )
        plugin_item.setData(status, ROLES.PLUGIN_STATUS)
        plugin_item.setData(str(plugin_data['name']), ROLES.PLUGIN_NAME)
        new_plugin_version = parse_version(plugin_data['version'])
        plugin_item.setData(new_plugin_version, ROLES.PLUGIN_VERSION)
        plugin_item.setData(plugin_id, ROLES.PLUGIN_ID)
        plugin_item.setIcon(STATUS_ICONS[status])

        if plugin_data['incompatible'] or plugin_data['deprecated']:
            if plugin_data['incompatible']:
                plugin_item.setIcon(
                    QtGui.QIcon(qta.icon('mdi6.alert-circle-outline'))
                )
                plugin_item.setText(f'{plugin_item.text()} [Incompatible]')
                plugin_item.setData(True, ROLES.PLUGIN_INCOMPATIBLE)
            else:
                plugin_item.setIcon(QtGui.QIcon(qta.icon('mdi6.alert')))
                plugin_item.setText(f'{plugin_item.text()} [Deprecated]')
                plugin_item.setData(True, ROLES.PLUGIN_DEPRECATED)
        else:
            plugin_item.setIcon(STATUS_ICONS[status])

        # check if is a new plugin.....
        stored_item = self.plugin_is_available(plugin_data)

        if not stored_item:
            # add new plugin
            if status == STATUSES.INSTALLED:
                plugin_item.setData(
                    plugin_data['path'], ROLES.PLUGIN_INSTALLED_PATH
                )
                plugin_item.setEnabled(False)
                plugin_item.setCheckable(False)

            elif status in [STATUSES.NEW, STATUSES.DOWNLOAD]:
                plugin_item.setData(
                    plugin_data['path'], ROLES.PLUGIN_SOURCE_PATH
                )
                destination_path = os.path.join(
                    self.default_install_plugin_directory, destination_filename
                )
                plugin_item.setData(
                    destination_path, ROLES.PLUGIN_DESTINATION_PATH
                )

                if status is STATUSES.NEW:
                    # enable it by default as is new.
                    plugin_item.setCheckable(True)
                    plugin_item.setCheckState(QtCore.Qt.CheckState.Checked)

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
            destination_path = os.path.join(
                self.default_install_plugin_directory, destination_filename
            )
            stored_item.setData(
                destination_path, ROLES.PLUGIN_DESTINATION_PATH
            )
            stored_item.setData(plugin_data['path'], ROLES.PLUGIN_SOURCE_PATH)

            stored_item.setData(new_plugin_version, ROLES.PLUGIN_VERSION)

            # enable it by default if we are updating
            stored_item.setCheckable(True)
            stored_item.setEnabled(True)
            stored_item.setCheckState(QtCore.Qt.CheckState.Checked)

    def plugin_is_available(self, plugin_data):
        '''Return item from *plugin_data* if found.'''
        num_items = self._plugin_model.rowCount()
        for i in range(num_items):
            item = self._plugin_model.item(i)
            item_id = item.data(ROLES.PLUGIN_ID)
            if item_id == plugin_data['id']:
                return item
        return None

    def _remove_plugin(self, plugin_name):
        '''Remove the plugin *plugin_name* from plugin list (not disk),
        if succeeded/found True will be returned, False otherwise.'''
        num_items = self._plugin_model.rowCount()
        for i in range(num_items):
            item = self._plugin_model.item(i)
            item_name = item.data(ROLES.PLUGIN_NAME)
            if item_name == plugin_name:
                # Remove item
                self._plugin_model.takeRow(i)
                return True
        return False

    def populate_installed_plugins(self, plugins):
        '''Populate model with installed plugins.'''
        self._installed_plugin_count = 0
        self._plugin_model.clear()

        self._installed_plugins = []

        for plugin in plugins:
            try:
                self._add_plugin(plugin, STATUSES.INSTALLED)
                self._installed_plugins.append(plugin)
            except Exception as e:
                logger.exception(e)
                # Show message box to user
                QtWidgets.QMessageBox.warning(
                    self,
                    'Warning',
                    f'The following plugin failed to load:\n\n{plugin}\n\n{e}',
                )
                logger.warning(f'Failed to add plugin {plugin}: ')

    def populate_download_plugins(self, prereleases=False):
        '''Populate model with remotely configured plugins.'''
        # Read plugins from json config url if set by user
        self._downloadable_plugin_count = 0
        if self._json_config_url:
            # TODO: remove this when there is a way for users to point plugin manager
            # to their own repository releases
            response = urlopen(self._json_config_url)
            response_json = json.loads(response.read())

            for link in response_json['integrations']:
                self._add_plugin(get_plugin_data(link), STATUSES.DOWNLOAD)
                self._downloadable_plugin_count += 1
        else:
            url = os.environ.get(
                'FTRACK_CONNECT_GITHUB_RELEASES_URL',
                DEFAULT_INTEGRATIONS_REPO_URL,
            )
            if url.lower() in ['none', 'disable', '0', 'false']:
                logger.warning(
                    'Not attempting to fetch releases from Github, '
                    'disabled by environment variable.'
                )
                return
            # Read latest releases from ftrack integrations repository
            releases = fetch_github_releases(url, prereleases=prereleases)

            for release in releases:
                self._add_plugin(
                    get_plugin_data(release['url']), STATUSES.DOWNLOAD
                )
                self._downloadable_plugin_count += 1

    def archive_legacy_plugin(self, plugin_name):
        '''Move legacy plugin identified by *plugin_name* to archive folder'''
        install_path = os.path.join(
            self.default_install_plugin_directory, plugin_name
        )
        logger.debug(f'Archiving legacy plugin: {install_path}')
        if os.path.exists(install_path) and os.path.isdir(install_path):
            archive_base_path = os.path.relpath(
                os.path.join(
                    self.default_install_plugin_directory,
                    '..',
                    'ftrack-connect-plugins-ARCHIVED',
                )
            )
            archive_path = os.path.join(archive_base_path, plugin_name)
            remove = True
            if not os.path.exists(archive_base_path):
                remove = False
                os.makedirs(archive_base_path)
            elif not os.path.exists(archive_path):
                # Move it to archive
                try:
                    logger.warning(
                        f'Attempting to archive plugin: {install_path} > {archive_path}'
                    )
                    shutil.move(install_path, archive_path)
                    logger.warning(f'Archived plugin: {install_path}')
                    remove = False
                except Exception as e:
                    logger.exception(e)
                    logger.error(
                        f'Plugin archive failed, please check permissions! {e}'
                    )
            else:
                logger.warning(f'Plugin is already archived @ {archive_path}')
            if remove:
                logger.warning(f'Attempting to remove plugin: {install_path}')
                try:
                    shutil.rmtree(
                        install_path, ignore_errors=False, onerror=None
                    )
                    logger.warning(f'Removed plugin: {install_path}')
                except Exception as e:
                    logger.exception(e)
                    logger.error(
                        f'Plugin removal failed, please check permissions! {e}'
                    )

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
        event.setDropAction(QtCore.Qt.DropAction.CopyAction)
        event.accept()
        self._set_drop_zone_state('active')

    def dropEvent(self, event):
        '''Handle dropped file event.'''
        self._set_drop_zone_state()

        paths = self._process_mime_data(event.mimeData())

        for path in paths:
            # Remove existing one
            plugin_data = get_plugin_data(path)
            self._remove_plugin(plugin_data['name'])
            self._add_plugin(plugin_data, STATUSES.NEW)

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
