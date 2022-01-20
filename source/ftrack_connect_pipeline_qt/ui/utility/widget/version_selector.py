# :coding: utf-8
# :copyright: Copyright (c) 2014-2021 ftrack

import logging

from Qt import QtWidgets, QtCore, QtGui

from ftrack_connect_pipeline_qt.utils import BaseThread


class VersionComboBox(QtWidgets.QComboBox):
    versions_query_done = QtCore.Signal()

    def __init__(self, session, parent=None):
        super(VersionComboBox, self).__init__(parent=parent)
        self.logger = logging.getLogger(__name__ + '.' + self.__class__.__name__)

        self.setEditable(False)
        self.session = session
        self.context_id = None

        self.asset_entity = None

    def set_asset_entity(self, asset_entity):
        self.asset_entity = asset_entity
        self.clear()
        self._add_version(self.asset_entity['latest_version'])

    def showPopup(self):
        self.clear()
        versions = self.query_versions(self.context_id, self.asset_entity['id'])
        self.add_versions(versions)
        self.setCurrentIndex(0)
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
        self.addItem(str("Version {}".format(version['version'])), version['id'])

    def add_versions(self, versions):
        for version in versions:
            self._add_version(version)
        self.versions_query_done.emit()


class VersionSelector(QtWidgets.QWidget):

    version_changed = QtCore.Signal(object, object)

    def __init__(self, session, parent=None):
        super(VersionSelector, self).__init__(parent=parent)
        self.logger = logging.getLogger(__name__ + '.' + self.__class__.__name__)
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
        self.version_combobox.currentIndexChanged.connect(self._current_version_changed)
        self.version_combobox.editTextChanged.connect(self._current_version_changed)

    def _current_version_changed(self, index):
        if index == -1:
            return
        version_num = self.version_combobox.currentText().split("Version ")[1]
        current_idx = self.version_combobox.currentIndex()
        version_id = self.version_combobox.itemData(current_idx)
        self.version_changed.emit(version_num, version_id)

    def set_context_id(self, context_id):
        self.logger.debug('setting context to :{}'.format(context_id))
        self.version_combobox.set_context_id(context_id)

    def set_asset_entity(self, asset_entity):
        self.logger.debug('setting asset_id to :{}'.format(asset_entity))
        self.version_combobox.set_asset_entity(asset_entity)
