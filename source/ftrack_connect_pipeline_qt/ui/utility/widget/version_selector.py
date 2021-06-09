import logging
from Qt import QtWidgets, QtCore, QtGui


class VersionComboBox(QtWidgets.QComboBox):

    def __init__(self, session, parent=None):
        super(VersionComboBox, self).__init__(parent=parent)
        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )
        self.setEditable(True)
        self.session = session
        self.context_entity = None

    def context_changed(self, context_entity):
        self.context_entity = context_entity
        self.clear()

    def asset_changed(self, asset_id):
        self.clear()
        versions = self.session.query(
            'select version '
            'from AssetVersion where task.id is {} and asset_id is {} order by'
            ' version descending'.format(self.context_entity['id'], asset_id)).all()
        for version in versions:
            self.addItem(str(version['version']), version['id'])


class VersionSelector(QtWidgets.QWidget):

    version_changed = QtCore.Signal(object, object)

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
        main_layout = QtWidgets.QVBoxLayout()
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
            self._current_version_changed)

    def _current_version_changed(self, index):
        version_num = self.version_combobox.currentText()
        current_idx = self.version_combobox.currentIndex()
        version_id = self.version_combobox.itemData(current_idx)
        self.version_changed.emit(version_num, version_id)

    def set_context(self, context_entity):
        self.logger.debug('setting context to :{}'.format(context_entity))
        self.version_combobox.context_changed(context_entity)

    def set_asset_id(self, asset_id):
        self.logger.debug('setting asset_id to :{}'.format(asset_id))
        self.version_combobox.asset_changed(asset_id)
