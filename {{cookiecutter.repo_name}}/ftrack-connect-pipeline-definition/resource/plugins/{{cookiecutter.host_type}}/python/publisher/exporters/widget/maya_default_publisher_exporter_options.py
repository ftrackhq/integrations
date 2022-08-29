# :coding: utf-8
# :copyright: Copyright (c) 2014-{{cookiecutter.year}} ftrack

from functools import partial

from ftrack_connect_pipeline_{{cookiecutter.host_type}} import plugin
from ftrack_connect_pipeline_qt.plugin.widgets.dynamic import DynamicWidget
from ftrack_connect_pipeline_qt.ui.utility.widget import group_box

from Qt import QtWidgets, QtCore

import ftrack_api


class {{cookiecutter.host_type|capitalize}}DefaultPublisherExporterOptionsWidget(DynamicWidget):
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

        self.options_cb = {}

        super({{cookiecutter.host_type|capitalize}}DefaultPublisherExporterOptionsWidget, self).__init__(
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
        '''build function , mostly used to create the widgets.'''

        options = {
            'constructionHistory': False,
            'channels': False,
            'preserveReferences': False,
            'shader': False,
            'constraints': False,
            'expressions': False,
        }
        # Update current options with the given ones from definitions
        options.update(self.options)

        self.option_group = group_box.GroupBox('{{cookiecutter.host_type|capitalize}} exporter Options')
        self.option_group.setToolTip(self.description)

        self.option_layout = QtWidgets.QVBoxLayout()
        self.option_group.setLayout(self.option_layout)

        self.file_type_combo = QtWidgets.QComboBox()
        self.file_type_combo.addItem('{{cookiecutter.host_type}}Binary (.mb)')
        self.file_type_combo.addItem('{{cookiecutter.host_type}}Ascii (.ma)')
        self.option_layout.addWidget(self.file_type_combo)

        # set current options as self.options
        self._options = options

        # Call the super build to automatically generate the options
        super({{cookiecutter.host_type|capitalize}}DefaultPublisherExporterOptionsWidget, self).build()

        self.layout().addWidget(self.option_group)

    def _register_widget(self, name, widget):
        '''Register *widget* with *name* and add it to main layout.'''
        # Overriding this method in order to attach the widget to the option_layout
        widget_layout = QtWidgets.QHBoxLayout()
        widget_layout.setContentsMargins(1, 2, 1, 2)
        widget_layout.setAlignment(QtCore.Qt.AlignTop)
        label = QtWidgets.QLabel(name)

        widget_layout.addWidget(label)
        widget_layout.addWidget(widget)
        self.option_layout.addLayout(widget_layout)

    def post_build(self):
        super({{cookiecutter.host_type|capitalize}}DefaultPublisherExporterOptionsWidget, self).post_build()

        self.file_type_combo.currentIndexChanged.connect(
            self._on_file_type_set
        )

    def _on_file_type_set(self, index):
        value = self.file_type_combo.currentText()
        self.set_option_result(value.split(' ')[0], 'type')


class {{cookiecutter.host_type|capitalize}}DefaultPublisherExporterOptionsPluginWidget(
    plugin.{{cookiecutter.host_type|capitalize}}PublisherExporterPluginWidget
):
    plugin_name = '{{cookiecutter.host_type}}_default_publisher_exporter'
    widget = {{cookiecutter.host_type|capitalize}}DefaultPublisherExporterOptionsWidget


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = {{cookiecutter.host_type|capitalize}}DefaultPublisherExporterOptionsPluginWidget(api_object)
    plugin.register()
