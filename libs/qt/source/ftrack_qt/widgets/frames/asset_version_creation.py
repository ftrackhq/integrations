# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from Qt import QtWidgets, QtCore, QtGui

from ftrack_qt.widgets.thumbnails import OpenAssetVersionThumbnail


class AssetVersionCreation(QtWidgets.QFrame):
    '''Widget representing the next version of the asset version'''

    @property
    def version(self):
        return self._versions[-1]

    def __init__(self, asset_name, versions):
        super(AssetVersionCreation, self).__init__()

        self._asset_name = asset_name
        self._versions = versions

        self._thumbnail_widget = None
        self._asset_name_widget = None
        self._create_label = None
        self._version_label = None

        self.pre_build()
        self.build()

    def pre_build(self):
        self.setLayout(QtWidgets.QHBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().setSpacing(5)

    def build(self):
        self._thumbnail_widget = OpenAssetVersionThumbnail()
        self._thumbnail_widget.setScaledContents(True)
        self._thumbnail_widget.setMinimumSize(57, 31)
        self._thumbnail_widget.setMaximumSize(57, 31)
        self._thumbnail_widget.set_server_url(self.version['server_url'])
        self._thumbnail_widget.load(self.version['thumbnail'])
        self.layout().addWidget(self._thumbnail_widget)

        self._asset_name_widget = QtWidgets.QLabel(self._asset_name)
        self.layout().addWidget(self._asset_name_widget)

        self._create_label = QtWidgets.QLabel('- create')
        self._create_label.setObjectName("gray")
        self.layout().addWidget(self._create_label)

        self._version_label = QtWidgets.QLabel(
            'Version {}'.format(self.version['version'] + 1)
        )
        self._version_label.setObjectName("color-primary")
        self.layout().addWidget(self._version_label)

        self.layout().addStretch()

        self.setToolTip(self._asset_name)
