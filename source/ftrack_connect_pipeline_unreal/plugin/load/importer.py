# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import unreal

from ftrack_connect_pipeline import plugin

from ftrack_connect_pipeline_qt import plugin as pluginWidget

from ftrack_connect_pipeline_unreal.plugin import (
    UnrealBasePlugin,
    UnrealBasePluginWidget,
)
from ftrack_connect_pipeline_unreal.utils import (
    custom_commands as unreal_utils,
)
from ftrack_connect_pipeline_unreal.constants.asset import modes as load_const
from ftrack_connect_pipeline_unreal.constants import asset as asset_const


class UnrealLoaderImporterPlugin(
    plugin.LoaderImporterPlugin, UnrealBasePlugin
):
    '''Class representing a Collector Plugin

    .. note::

        _required_output a List
    '''

    load_modes = load_const.LOAD_MODES

    dependency_load_mode = load_const.IMPORT_MODE

    @unreal_utils.run_in_main_thread
    def get_current_objects(self):
        return unreal_utils.get_current_scene_objects()

    def init_nodes(self, context_data=None, data=None, options=None):
        init_nodes_result = super(UnrealLoaderImporterPlugin, self).init_nodes(
            context_data=context_data, data=data, options=options
        )
        # Check if is snapshot
        is_snapshot = self.asset_info.get(asset_const.COMPONENT_PATH).endswith(
            ("uasset", "umap")
        )
        if is_snapshot:
            # Set asset_info as is napshot.
            self.ftrack_object_manager.is_snapshot = True
        return init_nodes_result

    def load_asset(self, context_data=None, data=None, options=None):
        '''(Override) Load without connecting objects for assets'''

        asset_info = options.get('asset_info')
        if not asset_info.get(asset_const.IS_SNAPSHOT):
            # Pipeline asset load, proceed as normal
            return super(UnrealLoaderImporterPlugin, self).load_asset(
                context_data, data, options
            )

        self.asset_info = asset_info
        dcc_object = self.DccObject(
            from_id=asset_info[asset_const.ASSET_INFO_ID]
        )
        self.dcc_object = dcc_object
        # Remove asset_info from the options as it is not needed anymore
        options.pop('asset_info')
        # Execute the run method to load the objects
        run_result = self.run(context_data, data, options)

        # Set asset_info as loaded.
        self.ftrack_object_manager.objects_loaded = True

        result = {
            'asset_info': self.asset_info,
            'dcc_object': self.dcc_object,
            'result': run_result,
        }

        return result


class UnrealLoaderImporterPluginWidget(
    pluginWidget.LoaderImporterPluginWidget, UnrealBasePluginWidget
):
    '''Class representing a Collector Widget

    .. note::

        _required_output a List
    '''
