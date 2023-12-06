# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from Qt import QtWidgets, QtCore, QtGui

from ftrack_qt.widgets.thumbnails import AssetVersionThumbnail


class AssetVersionCreation(QtWidgets.QFrame):
    '''Widget representing the next version of the asset version'''

    @property
    def version(self):
        '''Return the latest version of the asset.'''
        if not self._versions:
            return None
        return self._versions[-1]

    def __init__(self, asset_name, asset_id, versions, server_url):
        '''Initialize the AssetVersionCreation widget.'''
        super(AssetVersionCreation, self).__init__()

        self._asset_id = asset_id
        self._asset_name = asset_name
        self._versions = versions
        self._server_url = server_url

        self._thumbnail_widget = None
        self._asset_name_widget = None
        self._create_label = None
        self._version_label = None

        self.pre_build()
        self.build()

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
        # TODO: use place holder in case no version
        self._thumbnail_widget.set_server_url(self._server_url)
        if self.version:
            self._thumbnail_widget.load(self.version['thumbnail'])
        self.layout().addWidget(self._thumbnail_widget)

        self._asset_name_widget = QtWidgets.QLabel(self._asset_name)
        self.layout().addWidget(self._asset_name_widget)

        self._create_label = QtWidgets.QLabel('- create')
        self._create_label.setObjectName("gray")
        self.layout().addWidget(self._create_label)

        self._version_label = QtWidgets.QLabel(
            'Version {}'.format(
                self.version['next_version'] if self.version else "a"
            )
        )
        self._version_label.setObjectName("color-primary")
        self.layout().addWidget(self._version_label)

        self.layout().addStretch()

        self.setToolTip(self._asset_name)
