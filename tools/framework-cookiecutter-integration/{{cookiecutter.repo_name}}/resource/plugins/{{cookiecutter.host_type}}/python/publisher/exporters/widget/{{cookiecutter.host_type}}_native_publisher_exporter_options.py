# :coding: utf-8
# :copyright: Copyright (c) 2014-{{cookiecutter.year}} ftrack

from functools import partial

from ftrack_connect_pipeline_{{cookiecutter.host_type}} import plugin
from ftrack_connect_pipeline_qt.plugin.widget.dynamic import DynamicWidget
from ftrack_connect_pipeline_qt.ui.utility.widget import group_box

from Qt import QtWidgets, QtCore

import ftrack_api


class {{cookiecutter.host_type_capitalized}}NativePublisherExporterOptionsWidget(DynamicWidget):
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

        super({{cookiecutter.host_type_capitalized}}NativePublisherExporterOptionsWidget, self).__init__(
            parent=parent,
            session=session,
            data=data,
            name=name,
            description=description,
            options=options,
            context_id=context_id,
            asset_type_name=asset_type_name,
        )

    def define_options(self):
        '''Default renderable options for dynamic widget'''
        return {
            'constructionHistory': False,
            'channels': False,
            'preserveReferences': False,
            'shader': False,
            'constraints': False,
            'expressions': False,
            'type': [
                {
                    'label': 'mayaBinary (.mb)',
                    'value': 'mayaBinary',
                    'default': True,
                },
                {
                    'label': 'mayaAscii (.ma)',
                    'value': 'mayaAscii',
                },
            ],
        }


    def get_options_group_name(self):
        '''Override'''
        return '{{cookiecutter.host_type_capitalized}} exporter Options'

    def build(self):
        '''build function , mostly used to create the widgets.'''

        # Update current options with the given ones from definitions and store
        self.update(self.define_options())

        # Call the super build to automatically generate the options
        super({{cookiecutter.host_type_capitalized}}NativePublisherExporterOptionsWidget, self).build()


class {{cookiecutter.host_type_capitalized}}NativePublisherExporterOptionsPluginWidget(
    plugin.{{cookiecutter.host_type_capitalized}}PublisherExporterPluginWidget
):
    plugin_name = '{{cookiecutter.host_type}}_native_publisher_exporter'
    widget = {{cookiecutter.host_type_capitalized}}NativePublisherExporterOptionsWidget


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = {{cookiecutter.host_type_capitalized}}NativePublisherExporterOptionsPluginWidget(api_object)
    plugin.register()
