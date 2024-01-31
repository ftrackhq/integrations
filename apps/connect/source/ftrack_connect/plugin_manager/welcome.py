# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import platformdirs
import os
import logging
import urllib.request
import zipfile
import json
import tempfile
import qtawesome as qta

from ftrack_connect.qt import QtCore, QtWidgets, QtGui

from ftrack_utils.decorators import asynchronous

import ftrack_connect
from ftrack_connect.util import (
    get_plugin_json_url_from_environment,
    fetch_github_releases,
    get_platform_identifier,
)


class WelcomeDialog(QtWidgets.QDialog):
    '''Welcome plugin dialog - handles empty plugin folder'''

    plugins_installed = QtCore.Signal()
    installing = QtCore.Signal()
    # local variables for finding and installing plugin manager.
    install_path = platformdirs.user_data_dir(
        'ftrack-connect-plugins', 'ftrack'
    )

    json_config_url = get_plugin_json_url_from_environment()

    @property
    def skipped(self):
        return self._skipped

    def _discover_plugins(self):
        '''Provide plugin urls to download'''
        # Read plugins from json config url if set by user
        # TODO: remove this when there is a way for users to point plugin manager
        # to their own repository releases
        if self.json_config_url:
            with urllib.request.urlopen(self.json_config_url) as url:
                data = json.loads(url.read().decode())
                plugins_url = data.get('integrations')

                if not plugins_url:
                    self._install_button.setVisible(False)
                    self._skip.setVisible(False)
        else:
            # Read latest releases from ftrack integrations repository
            releases = fetch_github_releases()
            plugins_url = []
            for release in releases:
                plugins_url.append(release['url'])

        return plugins_url

    def _download_plugins(self, source_paths):
        '''Download plugins from provided *source_paths* item.'''
        temp_paths = []
        self._overlay.message = f"Downloaded 0/{len(source_paths)} plugins."
        i = 1
        for source_path in source_paths:
            zip_name = os.path.basename(source_path)
            save_path = tempfile.gettempdir()
            temp_path = os.path.join(save_path, zip_name)
            logging.debug(
                'Downloading {} to {}'.format(source_path, temp_path)
            )

            with urllib.request.urlopen(source_path) as dl_file:
                with open(temp_path, 'wb') as out_file:
                    out_file.write(dl_file.read())
            temp_paths.append(temp_path)
            self._overlay.message = (
                f"Downloaded {i}/{len(source_paths)} plugins."
            )
            i += 1
        return temp_paths

    @asynchronous
    def _install_plugins(self):
        '''Install all available plugins'''
        self._skipped = False
        self.installing.emit()
        plugins_path = self._discover_plugins()
        self._overlay.message = f"Discovered {len(plugins_path)} plugins."
        source_paths = self._download_plugins(plugins_path)
        self._overlay.message = f"Installed 0/{len(source_paths)} plugins."
        i = 1
        for source_path in source_paths:
            plugin_name = os.path.basename(source_path).split('.zip')[0]
            # If platform dependent plugin, remove platform identifier before installing
            plugin_name = plugin_name.replace(
                f'-{get_platform_identifier()}.', '.'
            )

            destination_path = os.path.join(self.install_path, plugin_name)
            logging.debug(
                'Installing {} to {}'.format(source_path, destination_path)
            )

            with zipfile.ZipFile(source_path, 'r') as zip_ref:
                zip_ref.extractall(destination_path)
            self._overlay.message = (
                f"Installed {i}/{len(source_paths)} plugins."
            )
            i += 1

        self.plugins_installed.emit()

    def _on_skip_callback(self):
        '''Skip plugin installation and proceed to connect'''
        self.close()

    def _on_plugins_installed(self):
        self._install_button.setVisible(False)
        self._skip.setVisible(False)
        self._restart_button.setVisible(True)
        self._overlay.hide()

    def _on_plugins_installing(self):
        self._overlay.show()

    def __init__(self, on_restart_callback, parent=None):
        '''Instantiate the actions widget.'''
        super(WelcomeDialog, self).__init__(parent=parent)
        self._skipped = True

        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(30, 0, 30, 0)
        self.setLayout(layout)
        spacer = QtWidgets.QSpacerItem(
            0,
            70,
            QtWidgets.QSizePolicy.Minimum,
            QtWidgets.QSizePolicy.Expanding,
        )
        layout.addItem(spacer)

        icon_label = QtWidgets.QLabel()
        icon = qta.icon(
            "ph.rocket", color='#FFDD86', rotated=45, scale_factor=0.7
        )
        icon_label.setPixmap(
            icon.pixmap(icon.actualSize(QtCore.QSize(180, 180)))
        )
        icon_label.setAlignment(QtCore.Qt.AlignCenter | QtCore.Qt.AlignTop)

        label_title = QtWidgets.QLabel("<H1>Let's get started!</H1>")
        label_title.setAlignment(QtCore.Qt.AlignCenter | QtCore.Qt.AlignTop)

        label_text = QtWidgets.QLabel(
            'To be able to get use of the connect application, '
            'you will need to install the plugins for the integrations you would like to use.'
            '<br/><br/>'
        )
        self._install_button = QtWidgets.QPushButton(
            'Install all the available plugins.'
        )
        self._skip = QtWidgets.QPushButton('Skip for now')
        self._install_button.setObjectName('primary')

        self._restart_button = QtWidgets.QPushButton('Restart Now')

        self._restart_button.setObjectName('primary')
        self._restart_button.setVisible(False)

        label_text.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop)
        label_text.setWordWrap(True)

        layout.addWidget(
            label_title, QtCore.Qt.AlignCenter | QtCore.Qt.AlignTop
        )
        layout.addWidget(
            icon_label, QtCore.Qt.AlignCenter | QtCore.Qt.AlignTop
        )
        layout.addWidget(
            label_text, QtCore.Qt.AlignCenter | QtCore.Qt.AlignTop
        )
        layout.addWidget(self._install_button)
        layout.addWidget(self._skip)
        layout.addWidget(self._restart_button)

        spacer = QtWidgets.QSpacerItem(
            0,
            300,
            QtWidgets.QSizePolicy.Minimum,
            QtWidgets.QSizePolicy.Expanding,
        )
        layout.addItem(spacer)
        self._install_button.clicked.connect(self._install_plugins)
        self._skip.clicked.connect(self._on_skip_callback)
        self.plugins_installed.connect(self._on_plugins_installed)
        self.installing.connect(self._on_plugins_installing)
        self._restart_button.clicked.connect(on_restart_callback)

        self._overlay = ftrack_connect.ui.widget.overlay.BusyOverlay(
            self, message='Installing'
        )
        self._overlay.hide()

        self.resize(350, 700)

        # Set as modal
        self.setModal(True)
