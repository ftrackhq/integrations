import logging
from Qt import QtWidgets, QtCore, QtGui
from ftrack_connect_pipeline_qt.utils import BaseThread


class AssetComboBox(QtWidgets.QComboBox):
    valid_asset_name = QtCore.QRegExp('[A-Za-z0-9_]+')

    def __init__(self, session, parent=None):
        super(AssetComboBox, self).__init__(parent=parent)
        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )
        self.setEditable(True)

        self.session = session

        validator = QtGui.QRegExpValidator(self.valid_asset_name)
        self.setValidator(validator)

    def query_assets_from_context(self, context_id, asset_type_name):
        asset_type_entity = self.session.query(
                    'select name from AssetType where short is "{}"'.format(asset_type_name)
                ).first()
        assets = self.session.query(
            'select name, versions.task.id , type.id '
            'from Asset where versions.task.id is {} and type.id is {}'.format(
                context_id, asset_type_entity['id'])
        ).all()
        return assets

    def add_assets_to_ui(self, assets):
        for asset in assets:
            self.addItem(asset['name'], asset['id'])

    def on_context_changed(self, context_id, asset_type_name):
        self.clear()

        thread = BaseThread(
            name='get_assets_thread',
            target=self.query_assets_from_context,
            callback=self.add_assets_to_ui,
            target_args=(context_id, asset_type_name)
        )
        thread.start()

    def validate_name(self):
        is_valid_bool = True
        if self.validator():
            asset_name = self.currentText()
            is_valid = self.validator().validate(asset_name, 0)
            if is_valid[0] != QtGui.QValidator.Acceptable:
                is_valid_bool = False
                self.setStyleSheet("border: 1px solid red;")
            else:
                is_valid_bool = True
                self.setStyleSheet("")
        return is_valid_bool


class AssetSelector(QtWidgets.QWidget):

    asset_changed = QtCore.Signal(object, object, object)

    def __init__(self, session, parent=None):
        super(AssetSelector, self).__init__(parent=parent)
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
        self.asset_name_label = QtWidgets.QLabel("Asset Name")
        self.asset_combobox = AssetComboBox(self.session)
        self.layout().addWidget(self.asset_name_label)
        self.layout().addWidget(self.asset_combobox)

    def post_build(self):
        self.asset_combobox.currentIndexChanged.connect(
            self._current_asset_changed
        )
        self.asset_combobox.editTextChanged.connect(self._current_asset_changed)

    def _current_asset_changed(self, index):
        asset_name = self.asset_combobox.currentText()
        is_valid_name = self.asset_combobox.validate_name()
        current_idx = self.asset_combobox.currentIndex()
        asset_id = self.asset_combobox.itemData(current_idx)
        self.asset_changed.emit(asset_name, asset_id, is_valid_name)

    def set_context(self, context_id, asset_type_name):
        self.logger.debug('setting context to :{}'.format(context_id))
        self.asset_combobox.on_context_changed(context_id, asset_type_name)
