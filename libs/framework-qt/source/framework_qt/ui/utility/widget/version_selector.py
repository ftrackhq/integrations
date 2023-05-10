# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack
import logging

from Qt import QtWidgets, QtCore, QtGui


class VersionComboBox(QtWidgets.QComboBox):
    '''The version selector combobox within VersionSelector widget'''

    versionsQueryDone = QtCore.Signal()
    versionChanged = QtCore.Signal(
        object
    )  # User has selected the version, version id as the argument
    filterMessage = QtCore.Signal(
        object
    )  # Version could not be chosen due to filter

    def __init__(self, session, filters=None, parent=None):
        super(VersionComboBox, self).__init__(parent=parent)
        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )

        self.session = session
        self._filters = filters

        self.setEditable(False)
        self.context_id = None
        self.asset_entity = None
        self._version_id = None

        self._mute_index_change_signal = False
        self.currentIndexChanged.connect(self._on_current_index_changed)

        self.setMaximumHeight(24)
        self.setMinimumHeight(24)

    def get_versions(self):
        '''Return all versions, as tuple (version, is_compatible) where is_compatible
        is True if version matches the supplied filter'''
        result = []
        if self._filters:
            component_names_filter = self._filters.get('component_names')
            file_types_filter = self._filters.get('file_types')
            for version in self.session.query(
                'select components.name,components.file_type,version from AssetVersion where asset.id is {}'.format(
                    self.asset_entity['id']
                )
            ):
                components = version['components']

                has_compatible_component = False
                if components:
                    for component in components:
                        name_compatible = file_type_compatible = False
                        if (
                            component_names_filter is None
                            or component['name'] in component_names_filter
                        ):
                            name_compatible = True
                        if (
                            file_types_filter is None
                            or component['file_type'] in file_types_filter
                        ):
                            file_type_compatible = True
                        if name_compatible and file_type_compatible:
                            has_compatible_component = True
                            break
                result.append((version, has_compatible_component))
        else:
            for version in self.session.query(
                'select version, id '
                'from AssetVersion where task.id is {} and asset_id is {} order by'
                ' version descending'.format(
                    self.context_id, self.asset_entity['id']
                )
            ).all():
                result.append((version, True))
        return result

    def set_asset_entity(self, asset_entity):
        self.asset_entity = asset_entity
        self._version_id = self._version_nr = None
        self.clear()
        latest_version = None
        if self._filters is None:
            latest_version = self.asset_entity['latest_version']
        else:
            for version, is_compatible in self.get_versions():
                if is_compatible:
                    if (
                        latest_version is None
                        or latest_version['version'] < version['version']
                    ):
                        latest_version = version
        if latest_version:
            self._add_version((latest_version, True))
            self._version_id = latest_version['id']
            self._version_nr = latest_version['version']
        return latest_version

    def set_version_entity(self, version_entity, is_compatible=True):
        self.asset_entity = version_entity['asset']
        self.clear()
        self._add_version((version_entity, is_compatible))
        self._version_id = version_entity['id']
        self._version_nr = version_entity['version']

    def showPopup(self):
        '''Override'''
        versions = self.get_versions()
        if len(versions) != self.count():
            self._mute_index_change_signal = True
            self.clear()
            self.add_versions(sorted(versions, key=lambda t: -t[0]['version']))
            self._mute_index_change_signal = False
        super(VersionComboBox, self).showPopup()

    def set_context_id(self, context_id):
        self.context_id = context_id
        self.clear()

    def _add_version(self, version_and_compatible_tuple):
        version, is_compatible = version_and_compatible_tuple
        self.addItem(
            str('v{}'.format(version['version'])), version_and_compatible_tuple
        )

    def add_versions(self, versions):
        selected_index = 0
        for index, version_and_compatible_tuple in enumerate(versions):
            self._add_version(version_and_compatible_tuple)
            if version_and_compatible_tuple[0]['id'] == self._version_id:
                selected_index = index
        self.setCurrentIndex(selected_index)
        self.versionsQueryDone.emit()

    def _on_current_index_changed(self, index):
        '''Process user version selection, propagate to widget'''
        if self._mute_index_change_signal:
            return
        self._version_id = self._version_nr = None
        if index > -1:
            version_and_compatible_tuple = self.itemData(index)
            (version, is_compatible) = version_and_compatible_tuple
            version_id = version['id']
            if version_id is not None and version_id != self._version_id:
                if is_compatible:
                    self._version_id = version_id
                    self._version_number = version['version']
                    self.versionChanged.emit(version_id)
                else:
                    self.filterMessage.emit(
                        '<html><i>- not compatible!</i></html>'.format(
                            version['version']
                        )
                    )
                    self.versionChanged.emit(None)


class VersionSelector(QtWidgets.QWidget):
    '''Version selector widget implemented by a combobox'''

    versionChanged = QtCore.Signal(
        object, object
    )  # User has selected the version

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
        '''Process user version selection, promote to event'''
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
