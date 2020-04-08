import logging
from Qt import QtWidgets, QtCore, QtGui


class VersionComboBox(QtWidgets.QComboBox):
    context_changed = QtCore.Signal(object)
    asset_changed = QtCore.Signal(object)

    def __init__(self, session, asset_id, parent=None):
        super(VersionComboBox, self).__init__(parent=parent)
        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )
        self.setEditable(True)
        self.asset_id = asset_id
        self.session = session
        self.context = None

        self.post_build()

    def post_build(self):
        self.context_changed.connect(self._on_context_changed)
        self.asset_changed.connect(self._on_asset_changed)

    def _on_context_changed(self, context):
        self.context = context
        self.clear()

    def _on_asset_changed(self, asset_id):
        self.asset_id = asset_id
        self.clear()
        versions = self.session.query(
            'select version '
            'from AssetVersion where task.id is {} and asset_id is {} order by'
            ' version descending'.format(self.context['id'], self.asset_id)).all()
        for version in versions:
            self.addItem(str(version['version']), version['id'])


class VersionSelector(QtWidgets.QWidget):

    version_changed = QtCore.Signal(object, object)

    def __init__(self, session, asset_id, parent=None):
        super(VersionSelector, self).__init__(parent=parent)
        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )
        self.logger.info('init version selector with : {}'.format(asset_id))

        self.session = session
        self.asset_id = asset_id

        self.pre_build()
        self.build()
        self.post_build()

    def pre_build(self):
        main_layout = QtWidgets.QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)

        self.setLayout(main_layout)

    def build(self):
        self.version_combobox = VersionComboBox(self.session, self.asset_id)
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

    def set_context(self, context):
        self.logger.info('setting context to :{}'.format(context))
        self.version_combobox.context_changed.emit(context)

    def set_asset_id(self, asset_id):
        self.logger.info('setting asset_id to :{}'.format(asset_id))
        self.version_combobox.asset_changed.emit(asset_id)
