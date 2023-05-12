# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

from ftrack_connect_pipeline_3dsmax import plugin
from ftrack_connect_pipeline_qt.plugin.widget.load_widget import (
    LoadBaseWidget,
)
from ftrack_connect_pipeline_3dsmax.constants.asset import modes as load_const
from ftrack_connect_pipeline_qt.ui.utility.widget import group_box

from Qt import QtWidgets
import ftrack_api


class MaxNativeLoaderImporterOptionsWidget(LoadBaseWidget):
    '''Max loader plugin widget'''

    load_modes = list(load_const.LOAD_MODES.keys())

    def __init__(
        self,
        parent=None,
        session=None,
        data=None,
        name=None,
        description=None,
        options=None,
        context_id=None,
        asset_type_name=None,
    ):
        super(MaxNativeLoaderImporterOptionsWidget, self).__init__(
            parent=parent,
            session=session,
            data=data,
            name=name,
            description=description,
            options=options,
            context_id=context_id,
            asset_type_name=asset_type_name,
        )

    def build(self):
        super(MaxNativeLoaderImporterOptionsWidget, self).build()

        self.options_gb = group_box.GroupBox('Options')
        options_lay = QtWidgets.QVBoxLayout()
        self.preserve_ref_cb = QtWidgets.QCheckBox('Preserve References')

        self.add_namespace_cb = QtWidgets.QCheckBox('Add Namespace')
        self.namespace_options_gb = group_box.GroupBox('Namespace Options')
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

        self.layout().addWidget(self.options_gb)

    def post_build(self):
        super(MaxNativeLoaderImporterOptionsWidget, self).post_build()

        self.preserve_ref_cb.stateChanged.connect(self._on_set_preserve_ref)

        self.add_namespace_cb.stateChanged.connect(
            self._on_namespace_status_changed
        )

        self.namespace_bg.buttonClicked.connect(
            self._on_namespace_option_changed
        )

        self.custom_name_le.textChanged.connect(self._on_set_custom_namespace)

    def set_defaults(self):
        super(MaxNativeLoaderImporterOptionsWidget, self).set_defaults()

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
        if radio_button.text() == load_const.OPEN_MODE:
            self.options_gb.hide()
        else:
            self.options_gb.show()
        super(
            MaxNativeLoaderImporterOptionsWidget, self
        )._on_load_mode_changed(radio_button)

    def _on_namespace_status_changed(self, value):
        '''Updates the options dictionary with provided *path* when
        textChanged of line_edit event is triggered'''
        if value:
            self.namespace_options_gb.show()
        else:
            self.namespace_options_gb.hide()
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


class MaxNativeLoaderImporterPluginWidget(
    plugin.MaxLoaderImporterPluginWidget
):
    plugin_name = 'max_native_loader_importer'
    widget = MaxNativeLoaderImporterOptionsWidget


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = MaxNativeLoaderImporterPluginWidget(api_object)
    plugin.register()
