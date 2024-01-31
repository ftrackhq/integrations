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


from ftrack_connect.qt import QtWidgets, QtCore, QtGui

from ftrack_connect.util import (
    qt_main_thread,
    is_conflicting_plugin,
    is_incompatible_plugin,
    is_deprecated_plugin,
    is_loadable_plugin,
    get_platform_identifier,
    get_plugin_json_url_from_environment,
    fetch_github_releases,
)

from ftrack_connect.plugin_manager.processor import (
    STATUSES,
    ROLES,
    STATUS_ICONS,
)


logger = logging.getLogger(__name__)


class DndPluginList(QtWidgets.QFrame):
    '''Plugin list widget'''

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

        # If set, download plugins from this url instead of the releases
        self._json_config_url = get_plugin_json_url_from_environment()

        self.default_plugin_directory = platformdirs.user_data_dir(
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
        '''Add provided *file_path* as plugin with given *status*.'''
        if not file_path:
            return

        data = self._is_plugin_valid(file_path)

        if not data:
            return

        # Check platform
        platform = get_platform_identifier()
        destination_filename = os.path.basename(file_path)
        if destination_filename.lower().endswith('.zip'):
            destination_filename = destination_filename[:-4]
        if data['platform'] != 'noarch':
            if data['platform'] != platform:
                # Not our platform, ask user if they want to install anyway
                msgbox = QtWidgets.QMessageBox(
                    QtWidgets.QMessageBox.Warning,
                    'Warning',
                    'This plugin is not compatible with your platform:'
                    f':\n\n{destination_filename}\n\nProceed install anyway?',
                    buttons=QtWidgets.QMessageBox.Yes
                    | QtWidgets.QMessageBox.No
                    | QtWidgets.QMessageBox.Cancel,
                    parent=self,
                )
                answer = msgbox.exec_()
                if answer == QtWidgets.QMessageBox.Yes:
                    pass
                elif answer == QtWidgets.QMessageBox.No:
                    return  # Skip this one, but proceed
                elif answer == QtWidgets.QMessageBox.Cancel:
                    raise Exception('Plugin installation cancelled by user.')

            if destination_filename.endswith(f'-{data["platform"]}'):
                destination_filename = destination_filename[
                    : -len(data["platform"]) - 1
                ]

        loadable = is_loadable_plugin(file_path)
        deprecated = is_deprecated_plugin(file_path)

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

        if not loadable or deprecated:
            if not loadable:
                plugin_item.setIcon(
                    QtGui.QIcon(qta.icon('mdi6.alert-circle-outline'))
                )
                plugin_item.setText(f'{plugin_item.text()} [Not loadable]')
            else:
                plugin_item.setIcon(QtGui.QIcon(qta.icon('mdi6.alert')))
                plugin_item.setText(f'{plugin_item.text()} [Deprecated]')
        else:
            plugin_item.setIcon(STATUS_ICONS[status])

        # check if is a new plugin.....
        stored_item = self.plugin_is_available(data)

        if not stored_item:
            # add new plugin
            if status == STATUSES.INSTALLED:
                plugin_item.setData(file_path, ROLES.PLUGIN_INSTALLED_PATH)
                plugin_item.setEnabled(False)
                plugin_item.setCheckable(False)

            elif status in [STATUSES.NEW, STATUSES.DOWNLOAD]:
                plugin_item.setData(file_path, ROLES.PLUGIN_SOURCE_PATH)
                destination_path = os.path.join(
                    self.default_plugin_directory, destination_filename
                )
                plugin_item.setData(
                    destination_path, ROLES.PLUGIN_DESTINATION_PATH
                )

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
            destination_path = os.path.join(
                self.default_plugin_directory, destination_filename
            )
            stored_item.setData(
                destination_path, ROLES.PLUGIN_DESTINATION_PATH
            )
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

        data['platform'] = 'noarch'
        if data['version'].lower().endswith('.zip'):
            # pop zip extension from the version.
            # TODO: refine regex to catch extension
            data['version'] = data['version'][:-4]
            parts = data['version'].split('-')
            if len(parts) > 1:
                data['version'] = parts[0]
                data['platform'] = parts[-1]

        return data

    @qt_main_thread
    def populate_installed_plugins(self, empty_plugins_callback=None):
        '''Populate model with installed plugins.'''
        self._plugin_model.clear()

        plugins = os.listdir(self.default_plugin_directory)

        for plugin in plugins:
            try:
                plugin_path = os.path.join(
                    self.default_plugin_directory, plugin
                )
                self.add_plugin(plugin_path, STATUSES.INSTALLED)
            except Exception as e:
                logger.exception(e)
                # Show message box to user
                QtWidgets.QMessageBox.warning(
                    self,
                    'Warning',
                    f'The following plugin failed to load:\n\n{plugin}\n\n{e}',
                )
                logger.warning(f'Failed to add plugin {plugin}: ')

        if empty_plugins_callback and len(plugins) == 0:
            empty_plugins_callback()

    @qt_main_thread
    def populate_download_plugins(self):
        '''Populate model with remotely configured plugins.'''

        if self._json_config_url:
            response = urlopen(self._json_config_url)
            response_json = json.loads(response.read())

            for link in response_json['integrations']:
                self.add_plugin(link, STATUSES.DOWNLOAD)
        else:
            # Read latest releases from ftrack integrations repository
            releases = fetch_github_releases()

            for release in releases:
                self.add_plugin(release['url'], STATUSES.DOWNLOAD)

    def get_conflicting_plugins(self):
        result = []
        plugins = os.listdir(self.default_plugin_directory)
        for plugin in plugins:
            plugin_path = os.path.join(self.default_plugin_directory, plugin)
            if is_conflicting_plugin(plugin_path):
                result.append(plugin)
        return result

    def get_incompatible_plugins(self):
        result = []
        plugins = os.listdir(self.default_plugin_directory)
        for plugin in plugins:
            plugin_path = os.path.join(self.default_plugin_directory, plugin)
            if is_incompatible_plugin(plugin_path):
                result.append(plugin)
        return result

    def get_deprecated_plugins(self):
        result = []
        plugins = os.listdir(self.default_plugin_directory)
        for plugin in plugins:
            plugin_path = os.path.join(self.default_plugin_directory, plugin)
            if is_deprecated_plugin(plugin_path):
                result.append(plugin)
        return result

    def archive_legacy_plugin(self, plugin_name):
        '''Move legacy plugin identified by *plugin_name* to archive folder'''
        install_path = os.path.join(self.default_plugin_directory, plugin_name)
        logger.debug(f'Archiving legacy plugin: {install_path}')
        if os.path.exists(install_path) and os.path.isdir(install_path):
            archive_base_path = os.path.relpath(
                os.path.join(
                    self.default_plugin_directory,
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
