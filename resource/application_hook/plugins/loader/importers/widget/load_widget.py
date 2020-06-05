# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

from ftrack_connect_pipeline_maya import plugin
from ftrack_connect_pipeline_qt.client.widgets.options import BaseOptionsWidget
from ftrack_connect_pipeline_maya.constants import asset as asset_const

from Qt import QtCore, QtWidgets


class LoadMayaWidget(BaseOptionsWidget):
    load_modes = [
        asset_const.OPEN_MODE,
        asset_const.IMPORT_MODE,
        asset_const.REFERENCE_MODE
    ]

    def __init__(
            self, parent=None, session=None, data=None, name=None,
            description=None, options=None, context=None
    ):
        super(LoadMayaWidget, self).__init__(
            parent=parent, session=session, data=data, name=name,
            description=description, options=options, context=context
        )

    def build(self):
        super(LoadMayaWidget, self).build()

        self.default_mode = self.options.get('load_mode', self.load_modes[0])
        self.default_options = self.options.get('load_options', {})
        self.button_group = QtWidgets.QButtonGroup(self)
        grid_lay = QtWidgets.QGridLayout()
        col_row = (0, 0)
        for mode in self.load_modes:
            r_b = QtWidgets.QRadioButton(mode)
            self.button_group.addButton(r_b)
            grid_lay.addWidget(r_b, col_row[0], col_row[1])
            if col_row[1] < 1:
                col_row = (col_row[0], col_row[1]+1)
            else:
                col_row = (col_row[0]+1, 0)

        self.options_gb = QtWidgets.QGroupBox('Options')
        options_lay = QtWidgets.QVBoxLayout()
        self.preserve_ref_cb = QtWidgets.QCheckBox('Preserve References')

        self.add_namespace_cb = QtWidgets.QCheckBox('Add Namespace')
        self.namespace_options_gb = QtWidgets.QGroupBox('Namespace Options')
        namespace_lay = QtWidgets.QVBoxLayout()
        self.namespace_bg = QtWidgets.QButtonGroup(self)
        file_name_rb = QtWidgets.QRadioButton('file_name')
        component_rb = QtWidgets.QRadioButton('component')
        custom_name_lay = QtWidgets.QHBoxLayout()
        self.custom_name_rb = QtWidgets.QRadioButton('custom')
        self.custom_name_le = QtWidgets.QLineEdit()

        self.namespace_bg.addButton(file_name_rb)
        self.namespace_bg.addButton(component_rb)
        self.namespace_bg.addButton(self.custom_name_rb)

        custom_name_lay.addWidget(self.custom_name_rb)
        custom_name_lay.addWidget(self.custom_name_le)

        namespace_lay.addWidget(file_name_rb)
        namespace_lay.addWidget(component_rb)
        namespace_lay.addLayout(custom_name_lay)

        self.namespace_options_gb.setLayout(namespace_lay)

        options_lay.addWidget(self.preserve_ref_cb)
        options_lay.addWidget(self.add_namespace_cb)
        options_lay.addWidget(self.namespace_options_gb)

        self.options_gb.setLayout(options_lay)

        self.layout().addLayout(grid_lay)
        self.layout().addWidget(self.options_gb)


    def post_build(self):
        super(LoadMayaWidget, self).post_build()

        self.button_group.buttonClicked.connect(
            self._on_load_mode_changed
        )

        self.preserve_ref_cb.stateChanged.connect(self._on_set_preserve_ref)

        self.add_namespace_cb.stateChanged.connect(
            self._on_namespace_status_changed
        )

        self.namespace_bg.buttonClicked.connect(
            self._on_namespace_option_changed
        )

        self.custom_name_le.textChanged.connect(self._on_set_custom_namespace)

        self._set_defaults()

    def _set_defaults(self):
        for button in self.button_group.buttons():
            if button.text() == self.default_mode:
                button.setChecked(True)
                self._on_load_mode_changed(button)

        self.add_namespace_cb.setChecked(
            self.default_options.get('add_namespace', False)
        )
        self._on_namespace_status_changed(self.add_namespace_cb.isChecked())

        self.preserve_ref_cb.setChecked(
            self.default_options.get('preserve_references', False)
        )
        self._on_set_preserve_ref(self.preserve_ref_cb.isChecked())

        custom = True
        for button in self.namespace_bg.buttons():
            if button.text() == self.default_options.get('namespace_option'):
                button.setChecked(True)
                self._on_namespace_option_changed(button)
                custom = False
                break
        if custom:
            self.custom_name_rb.setChecked(True)
            self.custom_name_le.setText(
                self.default_options.get('namespace_option')
            )
            self._on_namespace_option_changed(self.custom_name_rb)

    def _on_load_mode_changed(self, radio_button):
        '''set the result options of value for the key.'''
        if radio_button.text() == asset_const.OPEN_MODE:
            self.options_gb.hide()#setDisabled(True)
        else:
            self.options_gb.show()#setDisabled(False)
        self.set_option_result(radio_button.text(), key='load_mode')

    def _on_namespace_status_changed(self, value):
        '''Updates the options dictionary with provided *path* when
        textChanged of line_edit event is triggered'''
        if value:
            self.namespace_options_gb.show()#.setDisabled(False)
        else:
            self.namespace_options_gb.hide()#.setDisabled(True)
        self._update_load_options('add_namespace', value)

    def _on_namespace_option_changed(self, radio_button):
        key = 'namespace_option'
        value = radio_button.text()
        if radio_button.text() == 'custom':
            value = self.custom_name_le.text()
        self._update_load_options(key, value)

    def _on_set_custom_namespace(self, text):
        self._update_load_options('namespace_option', text)

    def _on_set_preserve_ref(self, checked):
        self._update_load_options('preserve_references', checked)

    def _update_load_options(self, k, v):
        self.default_options[k] = v
        self.set_option_result(self.default_options, key='load_options')

class LoadMayaPluginWidget(plugin.LoaderImporterMayaWidget):
    plugin_name = 'load_maya'
    widget = LoadMayaWidget


def register(api_object, **kw):
    plugin = LoadMayaPluginWidget(api_object)
    plugin.register()
