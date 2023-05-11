# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

import ftrack_api

from ftrack_connect_pipeline_maya import plugin
from ftrack_connect_pipeline_qt.plugin.widget.dynamic import DynamicWidget


class MayaNativePublisherExporterOptionsWidget(DynamicWidget):
    '''Maya native binary or ASCII publisher options user input plugin widget'''

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

        super(MayaNativePublisherExporterOptionsWidget, self).__init__(
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
        return 'Maya exporter Options'

    def build(self):
        '''build function , mostly used to create the widgets.'''

        # Update current options with the given ones from definitions and store
        self.update(self.define_options())

        # Call the super build to automatically generate the option widgets
        super(MayaNativePublisherExporterOptionsWidget, self).build()


class MayaNativePublisherExporterOptionsPluginWidget(
    plugin.MayaPublisherExporterPluginWidget
):
    plugin_name = 'maya_native_publisher_exporter'
    widget = MayaNativePublisherExporterOptionsWidget


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = MayaNativePublisherExporterOptionsPluginWidget(api_object)
    plugin.register()
