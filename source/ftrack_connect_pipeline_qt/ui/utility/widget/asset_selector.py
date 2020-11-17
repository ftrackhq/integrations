import logging
from Qt import QtWidgets, QtCore, QtGui


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

    def on_context_changed(self, context, asset_type):
        self.clear()

        assets = self.session.query(
            'select name, versions.task.id , type.id '
            'from Asset where versions.task.id is {} and type.id is {}'.format(
                context['id'], asset_type['id'])
        ).all()
        for asset in assets:
            self.addItem(asset['name'], asset['id'])


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
        is_valid_bool = True
        if self.asset_combobox.validator():
            is_valid = self.asset_combobox.validator().validate(asset_name, 0)
            if is_valid[0] != QtGui.QValidator.Acceptable:
                is_valid_bool = False
                pal = self.asset_combobox.palette()
                pal.setColor(
                    QtGui.QPalette.Button,
                    QtGui.QColor(255, 0, 0)
                )
                self.asset_combobox.setPalette(pal)
            else:
                is_valid_bool = True
                self.asset_combobox.setPalette(
                    self.asset_combobox.style().standardPalette()
                )
        current_idx = self.asset_combobox.currentIndex()
        asset_id = self.asset_combobox.itemData(current_idx)
        self.asset_changed.emit(asset_name, asset_id, is_valid_bool)

    def set_context(self, context, asset_type):
        self.logger.info('setting context to :{}'.format(context))
        self.asset_combobox.on_context_changed(context, asset_type)
