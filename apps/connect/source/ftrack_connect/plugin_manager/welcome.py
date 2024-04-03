# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import platformdirs
import qtawesome as qta

try:
    from PySide6 import QtWidgets, QtCore, QtGui
except ImportError:
    from PySide2 import QtWidgets, QtCore, QtGui

from ftrack_utils.decorators import asynchronous

import ftrack_connect
from ftrack_connect.utils.plugin import (
    get_plugin_json_url_from_environment,
)


class WelcomeDialog(QtWidgets.QDialog):
    '''Welcome plugin dialog - allow user to install all available plugins or skip.'''

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

    def __init__(self, install_all_callback, on_restart_callback, parent=None):
        '''Instantiate the welcome dialog. *install_all_callback* - callback for
        installing all plugins. *on_restart_callback* - callback for restarting
        the application after installation. *parent* - parent widget for the dialog
        '''
        super(WelcomeDialog, self).__init__(parent=parent)

        self._install_all_callback = install_all_callback
        self._on_restart_callback = on_restart_callback

        self._downloadable_plugin_count = 0
        self._skipped = True

        self._install_button = None
        self._skip = None
        self._restart_button = None
        self._overlay = None

        self.pre_build()
        self.build()
        self.post_build()

    def pre_build(self):
        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(30, 0, 30, 0)
        self.setLayout(layout)

    def build(self):
        spacer = QtWidgets.QSpacerItem(
            0,
            70,
            QtWidgets.QSizePolicy.Policy.Minimum,
            QtWidgets.QSizePolicy.Policy.Expanding,
        )
        self.layout().addItem(spacer)

        icon_label = QtWidgets.QLabel()
        icon = qta.icon(
            "ph.rocket", color='#FFDD86', rotated=45, scale_factor=0.7
        )
        icon_label.setPixmap(
            icon.pixmap(icon.actualSize(QtCore.QSize(180, 180)))
        )
        icon_label.setAlignment(
            QtCore.Qt.AlignmentFlag.AlignCenter
            | QtCore.Qt.AlignmentFlag.AlignTop
        )

        label_title = QtWidgets.QLabel("<H1>Let's get started!</H1>")
        label_title.setAlignment(
            QtCore.Qt.AlignmentFlag.AlignCenter
            | QtCore.Qt.AlignmentFlag.AlignTop
        )

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

        label_text.setAlignment(
            QtCore.Qt.AlignmentFlag.AlignLeft
            | QtCore.Qt.AlignmentFlag.AlignTop
        )
        label_text.setWordWrap(True)

        self.layout().addWidget(
            label_title,
            QtCore.Qt.AlignmentFlag.AlignCenter
            | QtCore.Qt.AlignmentFlag.AlignTop,
        )
        self.layout().addWidget(
            icon_label,
            QtCore.Qt.AlignmentFlag.AlignCenter
            | QtCore.Qt.AlignmentFlag.AlignTop,
        )
        self.layout().addWidget(
            label_text,
            QtCore.Qt.AlignmentFlag.AlignCenter
            | QtCore.Qt.AlignmentFlag.AlignTop,
        )
        self.layout().addWidget(self._install_button)
        self.layout().addWidget(self._skip)
        self.layout().addWidget(self._restart_button)

        spacer = QtWidgets.QSpacerItem(
            0,
            300,
            QtWidgets.QSizePolicy.Policy.Minimum,
            QtWidgets.QSizePolicy.Policy.Expanding,
        )
        self.layout().addItem(spacer)

    def post_build(self):
        self._install_button.clicked.connect(self._install_plugins)
        self._skip.clicked.connect(self._on_skip_callback)
        self.plugins_installed.connect(self._on_plugins_installed)
        self.installing.connect(self._on_plugins_installing)
        self._restart_button.clicked.connect(self._on_restart_callback)

        self._overlay = ftrack_connect.ui.widget.overlay.BusyOverlay(
            self, message='Installing'
        )
        self._overlay.hide()

        self.resize(350, 700)

        # Set as modal
        self.setModal(True)

    def set_downloadable_plugin_count(self, count):
        '''Set the total number of plugins that have been discovered.'''
        self._downloadable_plugin_count = count

    @asynchronous
    def _install_plugins(self):
        '''Install all available plugins by calling the plugin manager'''
        self._skipped = False
        self.installing.emit()
        self._overlay.message = (
            f"Discovered {self._downloadable_plugin_count} plugins."
        )
        self._overlay.message = (
            f"Installed 0/{self._downloadable_plugin_count} plugins."
        )

        def plugin_installed_callback(index):
            self._overlay.message = (
                f"Installed {index}/{self._downloadable_plugin_count} plugins."
            )

        self._install_all_callback(plugin_installed_callback)
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
