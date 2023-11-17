# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import logging

from Qt import QtWidgets, QtCore


class VersionSelector(QtWidgets.QComboBox):
    '''Version selector combobox'''

    versionsQueryDone = QtCore.Signal()
    versionChanged = QtCore.Signal(
        object
    )  # User has selected the version, version id as the argument

    @property
    def version(self):
        '''Return current selected asset version entity'''
        index = self.currentIndex()
        if index > -1:
            return self.itemData(index)
        else:
            return None

    def __init__(self, fetch_assetversions, parent=None):
        super(VersionSelector, self).__init__(parent=parent)
        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )

        self._fetch_assetversions = fetch_assetversions

        self.setEditable(False)
        self.context_id = None
        self.asset_entity = None

        self._version_id = None  # Current selected version id

        self._mute_index_change_signal = False
        self.currentIndexChanged.connect(self._on_current_index_changed)

        self.setMaximumHeight(24)
        self.setMinimumHeight(24)

    def get_versions(self):
        '''Return all versions beneath current asset'''
        return self._fetch_assetversions(self.asset_entity)

    def set_asset_entity(self, asset_entity):
        self.asset_entity = asset_entity
        self._version_id = None
        self.clear()
        latest_version = self.asset_entity['latest_version']
        if latest_version:
            self._add_version(latest_version)
            self._version_id = latest_version['id']
        return latest_version

    def set_version_entity(self, version_entity, is_compatible=True):
        self.asset_entity = version_entity['asset']
        self.clear()
        self._add_version((version_entity, is_compatible))
        self._version_id = version_entity['id']

    def showPopup(self):
        '''Override'''
        versions = self.get_versions()
        if len(versions) != self.count():
            self._mute_index_change_signal = True
            self.clear()
            self.add_versions(sorted(versions, key=lambda v: -v['version']))
            self._mute_index_change_signal = False
        super(VersionSelector, self).showPopup()

    def set_context_id(self, context_id):
        self.context_id = context_id
        self.clear()

    def _add_version(self, version):
        self.addItem(str('v{}'.format(version['version'])), version)

    def add_versions(self, versions):
        selected_index = 0
        for index, version in enumerate(versions):
            self._add_version(version)
            if version['id'] == self._version_id:
                selected_index = index
        self.setCurrentIndex(selected_index)
        self.versionsQueryDone.emit()

    def _on_current_index_changed(self, index):
        '''Process user version selection and emit signal'''
        if self._mute_index_change_signal:
            return
        self._version_id = None
        if index > -1:
            version = self.itemData(index)
            version_id = version['id']
            if version_id is not None and version_id != self._version_id:
                self._version_id = version_id
                self.versionChanged.emit(version)
