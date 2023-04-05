# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from ftrack_connect_pipeline_harmony import plugin
from ftrack_connect_pipeline_qt.plugin.widget.dynamic import DynamicWidget

import ftrack_api


class HarmonySequencePublisherExporterOptionsWidget(DynamicWidget):

    auto_fetch_on_init = False

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
        super(HarmonySequencePublisherExporterOptionsWidget, self).__init__(
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
            'image_format': [
                {'value': 'TVG'},
                {'value': 'TGA'},
                {'value': 'SGI'},
                {'value': 'PSD'},
                {'value': 'YUV'},
                {'value': 'PAL'},
                {'value': 'SCAN'},
                {'value': 'PNG', "default": True},
                {'value': 'JPG'},
                {'value': 'BMP'},
                {'value': 'OPT'},
                {'value': 'VAR'},
                {'value': 'TIFF'},
                {'value': 'DPX'},
                {'value': 'EXR'},
                {'value': 'PDF'},
                {'value': 'DTEX'},
            ]
        }

    def get_options_group_name(self):
        '''Override'''
        return 'Image sequence exporter options'

    def build(self):
        '''build function , mostly used to create the widgets.'''

        self.update(self.define_options())

        super(HarmonySequencePublisherExporterOptionsWidget, self).build()

    def on_fetch_callback(self, result):
        '''This function is called by the _set_internal_run_result function of
        the BaseOptionsWidget'''


class HarmonySequencePublisherExporterOptionsPluginWidget(
    plugin.HarmonyPublisherExporterPluginWidget
):
    plugin_name = 'harmony_sequence_publisher_exporter'
    widget = HarmonySequencePublisherExporterOptionsWidget


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = HarmonySequencePublisherExporterOptionsPluginWidget(api_object)
    plugin.register()
