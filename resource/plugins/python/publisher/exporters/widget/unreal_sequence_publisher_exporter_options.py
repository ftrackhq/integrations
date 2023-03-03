# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import ftrack_api

from ftrack_connect_pipeline_qt.plugin.widget.dynamic import DynamicWidget

from ftrack_connect_pipeline_unreal import plugin


class UnrealSequencePublisherExporterOptionsWidget(DynamicWidget):
    '''Unreal sequence publisher user input plugin widget'''

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
        super(UnrealSequencePublisherExporterOptionsWidget, self).__init__(
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
            'file_format': [
                {
                    'value': 'exr',
                    'default': True,
                },
                {'value': 'jpg'},
                {'value': 'bmp'},
                {'value': 'png'},
            ],
            'resolution': [
                {'value': '320x240(4:3)'},
                {'value': '640x480(4:3)'},
                {'value': '640x360(16:9)'},
                {
                    'value': '1280x720(16:9)',
                    'default': True,
                },
                {'value': '1920x1080(16:9)'},
                {'value': '3840x2160(16:9)'},
            ],
        }

    def get_options_group_name(self):
        '''Override'''
        return 'Unreal level sequence render options'

    def build(self):
        '''build function , mostly used to create the widgets.'''

        # Update current options with the given ones from definitions and store
        self.update(self.define_options())

        # Call the super build to automatically generate the options
        super(UnrealSequencePublisherExporterOptionsWidget, self).build()


class UnrealSequencePublisherExporterOptionsPluginWidget(
    plugin.UnrealPublisherExporterPluginWidget
):
    plugin_name = 'unreal_sequence_publisher_exporter'
    widget = UnrealSequencePublisherExporterOptionsWidget


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = UnrealSequencePublisherExporterOptionsPluginWidget(api_object)
    plugin.register()
