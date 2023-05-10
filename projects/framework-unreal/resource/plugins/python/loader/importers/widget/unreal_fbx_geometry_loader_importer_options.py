# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import ftrack_api

from framework_unreal import plugin
from framework_qt.plugin.widget.dynamic import DynamicWidget
from framework_unreal.constants.asset import modes as load_const


class UnrealFbxGeometryLoaderImporterOptionsWidget(DynamicWidget):
    '''Unreal FBX geometry loader plugin widget user input plugin widget.'''

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
        super(UnrealFbxGeometryLoaderImporterOptionsWidget, self).__init__(
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
            'ImportMaterials': False,
            'CreatePhysicsAsset': False,
            'OverrideFullName': True,
            'AutomatedImportShouldDetectType': False,
            'CombineMeshes': True,
            'RenameMesh': False,
            'RenameMeshPrefix': 'S_',
            'ReplaceExisting': True,
            'Automated': True,
            'Save': True,
        }

    def get_options_group_name(self):
        '''Override'''
        return 'FBX geometry loader Options'

    def build(self):
        '''build function , mostly used to create the widgets.'''

        self.update(self.define_options())

        super(UnrealFbxGeometryLoaderImporterOptionsWidget, self).build()


class UnrealFbxGeometryLoaderImporterOptionsPluginWidget(
    plugin.UnrealLoaderImporterPluginWidget
):
    plugin_name = 'unreal_fbx_geometry_loader_importer'
    widget = UnrealFbxGeometryLoaderImporterOptionsWidget


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = UnrealFbxGeometryLoaderImporterOptionsPluginWidget(api_object)
    plugin.register()
