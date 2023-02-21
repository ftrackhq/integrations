# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import unreal

import ftrack_api

from ftrack_connect_pipeline_unreal import plugin
from ftrack_connect_pipeline_qt.plugin.widget.dynamic import DynamicWidget
from ftrack_connect_pipeline_unreal.constants.asset import modes as load_const

from ftrack_connect_pipeline_unreal.utils import (
    node as unreal_node_utils,
)


class UnrealAbcAnimationLoaderImporterOptionsWidget(DynamicWidget):
    '''Unreal animation loader plugin widget user input plugin widget.'''

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
        super(UnrealAbcAnimationLoaderImporterOptionsWidget, self).__init__(
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
        result = {
            'Skeleton': [],
            'ImportMaterials': False,
            'UseCustomRange': False,
            'AnimRangeMin': 1,
            'AnimRangeMax': 100,
            'RenameAnim': False,
            'RenameAnimPrefix': 'A_',
            'ReplaceExisting': True,
            'Automated': True,
            'Save': True,
        }
        # Load existing skeletons
        skeletons = unreal_node_utils.get_asset_by_class('Skeleton')
        result['Skeleton'].append({'value': None})
        for skeleton in skeletons:
            result['Skeleton'].append({'value': str(skeleton.asset_name)})
        return result

    def get_options_group_name(self):
        '''Override'''
        return 'Alembic animation loader Options'

    def build(self):
        '''build function , mostly used to create the widgets.'''

        self.update(self.define_options())

        super(UnrealAbcAnimationLoaderImporterOptionsWidget, self).build()


class UnrealAbcAnimationLoaderImporterOptionsPluginWidget(
    plugin.UnrealLoaderImporterPluginWidget
):
    plugin_name = 'unreal_abc_animation_loader_importer'
    widget = UnrealAbcAnimationLoaderImporterOptionsWidget


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = UnrealAbcAnimationLoaderImporterOptionsPluginWidget(api_object)
    plugin.register()
