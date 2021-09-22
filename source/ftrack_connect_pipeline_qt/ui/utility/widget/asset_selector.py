import logging
from Qt import QtWidgets, QtCore, QtGui
from ftrack_connect_pipeline_qt.utils import BaseThread
from ftrack_connect_pipeline_qt.ui.utility.widget.radio_widget_button import (
    RadioVarticalWidgetButton, RadioHorizontalWidgetButton
)


class AssetComboBox(QtWidgets.QComboBox):
    # valid_asset_name = QtCore.QRegExp('[A-Za-z0-9_]+')
    assets_query_done = QtCore.Signal()

    def __init__(self, session, parent=None):
        super(AssetComboBox, self).__init__(parent=parent)
        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )

        self.session = session
        self.setMinimumWidth(200)
        self.setSizePolicy(
            QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.MinimumExpanding
        )

    def query_assets_from_context(self, context_id, asset_type_name):
        asset_type_entity = self.session.query(
                    'select name from AssetType where short is "{}"'.format(asset_type_name)
                ).first()
        assets = self.session.query(
            'select name, versions.task.id , type.id, id, latest_version,'
            'latest_version.version '
            'from Asset where versions.task.id is {} and type.id is {}'.format(
                context_id, asset_type_entity['id'])
        ).all()
        return assets

    def add_assets_to_ui(self, assets):
        for asset_entity in assets:
            self.addItem(
                "{} (to v{})".format(
                    asset_entity['name'], asset_entity['latest_version']['version']
                ),
                asset_entity
            )
        self.assets_query_done.emit()

    def on_context_changed(self, context_id, asset_type_name):
        self.clear()

        thread = BaseThread(
            name='get_assets_thread',
            target=self.query_assets_from_context,
            callback=self.add_assets_to_ui,
            target_args=(context_id, asset_type_name)
        )
        thread.start()


class AssetSelector(QtWidgets.QWidget):

    asset_changed = QtCore.Signal(object, object, object)
    valid_asset_name = QtCore.QRegExp('[A-Za-z0-9_]+')

    def __init__(self, session, is_loader=False, parent=None):
        super(AssetSelector, self).__init__(parent=parent)
        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )

        self.is_loader = is_loader
        self.session = session

        self.pre_build()
        self.build()
        self.post_build()

    def pre_build(self):
        main_layout = QtWidgets.QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(main_layout)

    def build(self):
        self.validator = QtGui.QRegExpValidator(self.valid_asset_name)

        main_label = QtWidgets.QLabel("Choose how to publish this new version")

        self.asset_combobox = AssetComboBox(self.session)
        self.asset_combobox.setValidator(self.validator)

        if self.is_loader:
            self.layout().addWidget(main_label)
            self.layout().addWidget(self.asset_combobox)
            return

        self.asset_combobox.setStyleSheet(
            "border: none;"
            "background-color: transparent;"
        )

        self.version_up_rb = RadioHorizontalWidgetButton(label="Version Up", widget=self.asset_combobox)




        self.new_asset_name = QtWidgets.QLineEdit()
        self.new_asset_name.setPlaceholderText("Asset Name...")
        self.new_asset_name.setValidator(self.validator)
        self.new_asset_name.setStyleSheet(
            "border: none;"
            "background-color: transparent;"
        )
        self.new_asset_name.setSizePolicy(
            QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Minimum
        )

        new_name_container = QtWidgets.QWidget()
        new_name_container.setContentsMargins(0, 0, 0, 0)
        text_layout = QtWidgets.QHBoxLayout()
        version_label = QtWidgets.QLabel("v1")
        version_label.setEnabled(False)
        new_name_container.setLayout(text_layout)
        new_name_container.layout().setContentsMargins(0, 0, 0, 0)

        new_name_container.layout().addWidget(self.new_asset_name)
        new_name_container.layout().addWidget(version_label)
        new_name_container.layout().addStretch()

        self.new_asset_rb = RadioVarticalWidgetButton(label="As a new asset", widget=new_name_container)

        button_group = QtWidgets.QButtonGroup()

        button_group.addButton(self.version_up_rb)
        button_group.addButton(self.new_asset_rb)

        self.layout().addWidget(main_label)
        self.layout().addWidget(self.version_up_rb)
        self.layout().addWidget(self.new_asset_rb)

        self.version_up_rb.setChecked(True)
        self.new_asset_rb.toggle_state()

    def post_build(self):
        self.asset_combobox.currentIndexChanged.connect(
            self._current_asset_changed
        )
        self.asset_combobox.assets_query_done.connect(self._pre_select_asset)
        if not self.is_loader:
            self.new_asset_name.textChanged.connect(self._new_assset_changed)
            self.version_up_rb.clicked.connect(self.toggle_rb_state)
            self.new_asset_rb.clicked.connect(self.toggle_rb_state)

    def toggle_rb_state(self):
        self.version_up_rb.toggle_state()
        self.new_asset_rb.toggle_state()
        if self.new_asset_rb.isChecked() and self.new_asset_name.text() == "":
            self.new_asset_name.setText(self.new_asset_name.placeholderText())
        elif not self.new_asset_rb.isChecked():
            self.new_asset_name.textChanged.disconnect()
            self.new_asset_name.setText("")
            self.new_asset_name.textChanged.connect(self._new_assset_changed)

    def _pre_select_asset(self):
        if self.asset_combobox.count() > 0:
            self.asset_combobox.setCurrentIndex(0)
            self.new_asset_rb.text_widget.setText("As a new asset")
            self.version_up_rb.show()
        if self.asset_combobox.count() <=0:
            self.version_up_rb.hide()
            self.new_asset_rb.text_widget.setText("Name")
            self.new_asset_rb.click()



    def _current_asset_changed(self, index):
        current_idx = self.asset_combobox.currentIndex()
        asset_entity = self.asset_combobox.itemData(current_idx)
        asset_name = asset_entity['name']
        is_valid_name = self.validate_name(asset_name)
        self.asset_changed.emit(asset_name, asset_entity, is_valid_name)

    def _new_assset_changed(self):
        asset_name = self.new_asset_name.text()
        is_valid_name = self.validate_name(asset_name)
        self.asset_changed.emit(asset_name, None, is_valid_name)

    def set_context(self, context_id, asset_type_name):
        self.logger.debug('setting context to :{}'.format(context_id))
        self.asset_combobox.on_context_changed(context_id, asset_type_name)
        self.propose_new_asset_placeholder_name(context_id)

    def _get_context_entity(self, context_id):
        context_entity = self.session.query(
            'select name from Context where id is "{}"'.format(context_id)
        ).first()
        return context_entity

    def propose_new_asset_placeholder_name(self, context_id):
        thread = BaseThread(
            name='get_assets_thread',
            target=self._get_context_entity,
            callback=self._set_placeholder_name,
            target_args=[context_id]
        )
        thread.start()

    def _set_placeholder_name(self, context_entity):
        self.new_asset_name.setPlaceholderText(
            context_entity.get("name", "New Asset Name...").replace(" ", "_")
        )

    def validate_name(self, asset_name):
        is_valid_bool = True
        if self.validator:
            is_valid = self.validator.validate(asset_name, 0)
            if is_valid[0] != QtGui.QValidator.Acceptable:
                is_valid_bool = False
                self.setStyleSheet("border: 1px solid red;")
            else:
                is_valid_bool = True
                self.setStyleSheet("")
        return is_valid_bool
