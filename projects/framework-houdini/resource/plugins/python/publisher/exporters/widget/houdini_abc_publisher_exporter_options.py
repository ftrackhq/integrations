# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import ftrack_api

from ftrack_connect_pipeline_houdini import plugin
from ftrack_connect_pipeline_qt.plugin.widget.dynamic import DynamicWidget


class HoudiniAbcPublisherExporterOptionsWidget(DynamicWidget):

    auto_fetch_on_init = True

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
        super(HoudiniAbcPublisherExporterOptionsWidget, self).__init__(
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
            "ABCFormat": ["Default", "HDF5", "Ogawa"],
            "ABCAnimation": False,
            "ABCFrameRangeStart": "1.0",
            "ABCFrameRangeEnd": "100.0",
            "ABCFrameRangeBy": "1.0",
        }

    def on_fetch_callback(self, result):
        '''This function is called by the _set_internal_run_result function of
        the BaseOptionsWidget'''
        # self._get_widget('ABCFrameRangeStart').setText(
        #    str(result['frameStart'])
        # )
        # self._get_widget('ABCFrameRangeEnd').setText(str(result['frameEnd']))

    def get_options_group_name(self):
        '''Override'''
        return 'Alembic exporter options'

    def build(self):
        '''build function , mostly used to create the widgets.'''

        self.update(self.define_options())

        super(HoudiniAbcPublisherExporterOptionsWidget, self).build()


class HoudiniAbcPublisherExporterOptionsPluginWidget(
    plugin.HoudiniPublisherExporterPluginWidget
):
    plugin_name = 'houdini_abc_publisher_exporter'
    widget = HoudiniAbcPublisherExporterOptionsWidget


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = HoudiniAbcPublisherExporterOptionsPluginWidget(api_object)
    plugin.register()
