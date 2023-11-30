# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from Qt import QtWidgets, QtCore, QtGui

from ftrack_qt.widgets.selectors.version_selector import VersionSelector
from ftrack_qt.widgets.thumbnails import AssetVersionThumbnail


class AssetVersionSelection(QtWidgets.QFrame):
    '''Widget representing an asset, with version selector, within the list,
    for user selection'''

    version_changed = QtCore.Signal(object)
    '''Signal emitted when version is changed, asset_version_id is passed'''

    @property
    def enable_version_select(self):
        '''Return if version_combobox is enabled'''
        return self._version_combobox.isEnabled()

    @enable_version_select.setter
    def enable_version_select(self, value):
        '''Set if version_combobox is enabled'''
        self._version_combobox.setEnabled(value)

    @property
    def version(self):
        '''Return selected version'''
        if self._version_combobox:
            return self._version_combobox.version

    def __init__(self, asset_name, versions):
        '''Initialize the AssetVersionSelection widget.'''
        super(AssetVersionSelection, self).__init__()

        self._asset_name = asset_name
        self._versions = versions

        self._thumbnail_widget = None
        self._asset_name_widget = None
        self._version_combobox = None
        self._version_info_widget = None

        self.pre_build()
        self.build()
        self.post_build()

    def pre_build(self):
        '''Set up the layout for the widget.'''
        self.setLayout(QtWidgets.QHBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().setSpacing(5)

    def build(self):
        '''Build the widget components.'''
        self._thumbnail_widget = AssetVersionThumbnail()
        self._thumbnail_widget.setScaledContents(True)
        self._thumbnail_widget.setMinimumSize(57, 31)
        self._thumbnail_widget.setMaximumSize(57, 31)
        self.layout().addWidget(self._thumbnail_widget)

        self._asset_name_widget = QtWidgets.QLabel(self._asset_name)
        self.layout().addWidget(self._asset_name_widget)

        self._version_combobox = VersionSelector()
        self._version_combobox.set_versions(self._versions)
        self._version_combobox.setMaximumHeight(20)
        self.layout().addWidget(self._version_combobox)

        self._version_info_widget = QtWidgets.QLabel()
        self._version_info_widget.setObjectName('gray')
        self.layout().addWidget(self._version_info_widget, 10)

        self._thumbnail_widget.set_server_url(
            self._version_combobox.version['server_url']
        )
        self._thumbnail_widget.load(
            self._version_combobox.version['thumbnail']
        )
        self._version_info_widget.setText(
            f"{self._version_combobox.version['user_first_name']} "
            f"{self._version_combobox.version['user_last_name']} @ "
            f"{self._version_combobox.version['date'].strftime('%y-%m-%d %H:%M')}"
        )

    def post_build(self):
        '''Connect signals after building the widget.'''
        self._version_combobox.currentIndexChanged.connect(
            self._on_current_version_changed
        )

    def _on_current_version_changed(self, index):
        '''Handle the event when the current version is changed.'''
        version_dict = self._version_combobox.version
        if version_dict:
            self.version_changed.emit(version_dict)
            self._thumbnail_widget.load(
                self._version_combobox.version['thumbnail']
            )
            self._version_info_widget.setText(
                f"{self._version_combobox.version['user_first_name']} "
                f"{self._version_combobox.version['user_last_name']} @ "
                f"{self._version_combobox.version['date'].strftime('%y-%m-%d %H:%M')}"
            )
