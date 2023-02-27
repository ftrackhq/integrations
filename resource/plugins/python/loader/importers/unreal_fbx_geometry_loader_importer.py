# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import unreal

import ftrack_api

from ftrack_connect_pipeline_unreal import plugin
from ftrack_connect_pipeline_unreal.constants.asset import modes as load_const
from ftrack_connect_pipeline_unreal import utils


class UnrealFbxGeometryLoaderImporterPlugin(
    plugin.UnrealGeometryLoaderImporterPlugin
):
    load_modes = load_const.LOAD_MODES

    plugin_name = 'unreal_fbx_geometry_loader_importer'

    def run(self, context_data=None, data=None, options=None):
        '''Load FBX geometry file pointed out by collected *data*, with *options*.'''

        # Build Unreal import task
        task, component_path = super(
            UnrealFbxGeometryLoaderImporterPlugin, self
        ).run(context_data, data, options)

        # Fbx geo specific options
        task.options = unreal.FbxImportUI()
        task.options.import_mesh = True
        task.options.import_as_skeletal = False
        task.options.import_materials = options.get('ImportMaterials', False)
        task.options.import_animations = False
        task.options.create_physics_asset = options.get(
            'CreatePhysicsAsset', False
        )
        task.options.override_full_name = options.get('OverrideFullName', True)
        task.options.automated_import_should_detect_type = options.get(
            'AutomatedImportShouldDetectType', False
        )
        task.options.mesh_type_to_import = (
            unreal.FBXImportType.FBXIT_STATIC_MESH
        )
        task.options.static_mesh_import_data = unreal.FbxStaticMeshImportData()
        task.options.static_mesh_import_data.set_editor_property(
            'combine_meshes', options.get('CombineMeshes', True)
        )

        results = {
            'component_path': self.import_geometry(options)
        }

        return results


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return

    fbx_geo_importer = UnrealFbxGeometryLoaderImporterPlugin(api_object)
    fbx_geo_importer.register()
