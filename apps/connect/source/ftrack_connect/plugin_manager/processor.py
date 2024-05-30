# :coding: utf-8
# :copyright: Copyright (c) 2014-2024 ftrack
import sys
import os
import shutil
import tempfile
import logging
import qtawesome as qta
import urllib
import traceback
import zipfile
from urllib.error import HTTPError

try:
    from PySide6 import QtWidgets, QtCore, QtGui
except ImportError:
    from PySide2 import QtWidgets, QtCore, QtGui
from ftrack_connect.utils.plugin import get_platform_identifier

logger = logging.getLogger(__name__)


class STATUSES(object):
    '''Store plugin statuses'''

    INSTALLED = 0
    NEW = 1
    UPDATE = 2
    REMOVE = 3
    DOWNLOAD = 4


class ROLES(object):
    '''Store plugin roles'''

    PLUGIN_STATUS = QtCore.Qt.ItemDataRole.UserRole + 1
    PLUGIN_NAME = PLUGIN_STATUS + 1
    PLUGIN_VERSION = PLUGIN_NAME + 1
    PLUGIN_SOURCE_PATH = PLUGIN_VERSION + 1
    PLUGIN_INSTALLED_PATH = PLUGIN_SOURCE_PATH + 1
    PLUGIN_DESTINATION_PATH = PLUGIN_INSTALLED_PATH + 1
    PLUGIN_ID = PLUGIN_DESTINATION_PATH + 1
    PLUGIN_INCOMPATIBLE = PLUGIN_ID + 1
    PLUGIN_DEPRECATED = PLUGIN_INCOMPATIBLE + 1


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
        platform = get_platform_identifier()

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

        destination_path = plugin.data(ROLES.PLUGIN_DESTINATION_PATH)
        logger.debug(f'Installing {source_path} to {destination_path}')

        with zipfile.ZipFile(source_path, 'r') as zip_ref:
            name_list = zip_ref.namelist()
            top_dir = name_list[0]
            zip_ref.extractall(destination_path)
            # Check if the top_dir matches the destination path
            if os.path.dirname(top_dir) == os.path.basename(destination_path):
                # Remove the top dir from the extracted files so we avoid duplicated folders.
                top_level_members = [
                    item
                    for item in name_list[1:]
                    if item[:-1].count(os.path.sep) <= 1
                ]
                for item in top_level_members:
                    shutil.move(
                        os.path.join(destination_path, item),
                        os.path.join(
                            destination_path, item.replace(top_dir, "")
                        ),
                    )
                # Remove the empty top directory
                os.rmdir(os.path.join(destination_path, top_dir))

    def remove(self, plugin):
        '''Remove provided *plugin* item.'''
        install_path = plugin.data(ROLES.PLUGIN_INSTALLED_PATH)
        logger.debug(f'Removing {install_path}')
        if (
            install_path
            and os.path.exists(install_path)
            and os.path.isdir(install_path)
        ):
            shutil.rmtree(install_path, ignore_errors=False, onerror=None)
        else:
            logger.warning(f'Could not remove {install_path} - not found!')
