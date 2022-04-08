# :coding: utf-8
# :copyright: Copyright (c) 2014-2021 ftrack

import logging

from Qt import QtWidgets, QtCore, QtGui

from ftrack_connect_pipeline_qt.utils import BaseThread


class VersionComboBox(QtWidgets.QComboBox):
    versionsQueryDone = QtCore.Signal()
    versionChanged = QtCore.Signal(object)

    def __init__(self, session, parent=None):
        super(VersionComboBox, self).__init__(parent=parent)
        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )

        self.setEditable(False)
        self.session = session
        self.context_id = None
        self.asset_entity = None
        self._version_id = None

        self.currentIndexChanged.connect(self._on_current_index_changed)

        self.setMaximumHeight(24)
        self.setMinimumHeight(24)

    def set_asset_entity(self, asset_entity):
        self.asset_entity = asset_entity
        self._version_nr = None
        self.clear()
        self._add_version(self.asset_entity['latest_version'])
        self._version_id = self.asset_entity['latest_version']['id']

    def set_version_entity(self, version_entity):
        self.asset_entity = version_entity['asset']
        self.clear()
        self._add_version(version_entity)
        self._version_id = version_entity['id']

    def showPopup(self):
        '''Override'''
        versions = self.query_versions(
            self.context_id, self.asset_entity['id']
        )
        if len(versions) != self.count():
            self.clear()
            self.add_versions(versions)
        super(VersionComboBox, self).showPopup()

    def set_context_id(self, context_id):
        self.context_id = context_id
        self.clear()

    def query_versions(self, context_id, asset_id):
        versions = self.session.query(
            'select version, id '
            'from AssetVersion where task.id is {} and asset_id is {} order by'
            ' version descending'.format(context_id, asset_id)
        ).all()
        return versions

    def _add_version(self, version):
        self.addItem(str('v{}'.format(version['version'])), version['id'])

    def add_versions(self, versions):
        selected_index = 0
        for index, version in enumerate(versions):
            self._add_version(version)
            if version['id'] == self._version_id:
                selected_index = index
        self.setCurrentIndex(selected_index)
        self.versionsQueryDone.emit()

    def _on_current_index_changed(self, index):
        if self._version_id is not None:
            version_id = self.itemData(index)
            if version_id is not None and version_id != self._version_id:
                self._version_id = version_id
                self.versionChanged.emit(
                    self.session.query(
                        'AssetVersion where id={}'.format(version_id)
                    ).first()
                )


class VersionSelector(QtWidgets.QWidget):

    versionChanged = QtCore.Signal(object, object)

    def __init__(self, session, parent=None):
        super(VersionSelector, self).__init__(parent=parent)
        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )
        self.session = session

        self.pre_build()
        self.build()
        self.post_build()

    def pre_build(self):
        main_layout = QtWidgets.QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)

        self.setLayout(main_layout)

    def build(self):
        self.asset_version_label = QtWidgets.QLabel("Asset Version")
        self.version_combobox = VersionComboBox(self.session)
        self.version_combobox.setEditable(False)
        self.layout().addWidget(self.asset_version_label)
        self.layout().addWidget(self.version_combobox)

    def post_build(self):
        self.version_combobox.currentIndexChanged.connect(
            self._current_version_changed
        )
        self.version_combobox.editTextChanged.connect(
            self._current_version_changed
        )

    def _current_version_changed(self, index):
        if index == -1:
            return
        version_num = self.version_combobox.currentText().split("Version ")[1]
        current_idx = self.version_combobox.currentIndex()
        version_id = self.version_combobox.itemData(current_idx)
        self.versionChanged.emit(version_num, version_id)

    def set_context_id(self, context_id):
        self.logger.debug('setting context to :{}'.format(context_id))
        self.version_combobox.set_context_id(context_id)

    def set_asset_entity(self, asset_entity):
        self.logger.debug('setting asset_id to :{}'.format(asset_entity))
        self.version_combobox.set_asset_entity(asset_entity)
