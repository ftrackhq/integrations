# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

from Qt import QtWidgets

import ftrack_api

from ftrack_connect_pipeline_qt import plugin as pluginWidget
from ftrack_connect_pipeline_qt.plugin.widget.load_widget import (
    LoadBaseWidget,
)
from ftrack_connect_pipeline_qt.ui.utility.widget import group_box


class CommonTestLoaderImporterOptionsWidget(LoadBaseWidget):
    '''Opener importer options user input test/template plugin widget'''

    load_modes = ['import', 'reference']

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
        super(CommonTestLoaderImporterOptionsWidget, self).__init__(
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
        super(CommonTestLoaderImporterOptionsWidget, self).build()

        self.options_gb = group_box.GroupBox('')
        options_lay = QtWidgets.QVBoxLayout()
        self.some_test_option_cb = QtWidgets.QCheckBox('Some test option')

        options_lay.addWidget(self.some_test_option_cb)

        self.options_gb.setLayout(options_lay)

        self.layout().addWidget(self.options_gb)

    def post_build(self):
        super(CommonTestLoaderImporterOptionsWidget, self).post_build()

        self.some_test_option_cb.stateChanged.connect(
            self._on_set_some_test_option
        )

    def set_defaults(self):
        super(CommonTestLoaderImporterOptionsWidget, self).set_defaults()

        self.some_test_option_cb.setChecked(
            self.default_options.get('some_test_option', False)
        )
        self._on_set_some_test_option(self.some_test_option_cb.isChecked())

    def _on_load_mode_changed(self, radio_button):
        '''set the result options of value for the key.'''
        super(
            CommonTestLoaderImporterOptionsWidget, self
        )._on_load_mode_changed(radio_button)

    def _on_set_some_test_option(self, checked):
        self._update_load_options('some_test_option', checked)

    def _update_load_options(self, k, v):
        self.default_options[k] = v
        self.set_option_result(self.default_options, key='load_options')


class CommonTestLoaderImporterPluginWidget(
    pluginWidget.LoaderImporterPluginWidget
):
    plugin_name = 'common_test_loader_importer'
    widget = CommonTestLoaderImporterOptionsWidget


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = CommonTestLoaderImporterPluginWidget(api_object)
    plugin.register()
