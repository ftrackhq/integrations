# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import unreal

import ftrack_api

from ftrack_framework_unreal import plugin
from ftrack_framework_unreal.constants.asset import modes as load_const


class UnrealFbxGeometryLoaderImporterPlugin(plugin.UnrealLoaderImporterPlugin):
    load_modes = load_const.LOAD_MODES

    plugin_name = 'unreal_fbx_geometry_loader_importer'

    def run(self, context_data=None, data=None, options=None):
        '''Load FBX geometry file pointed out by collected *data*, with *options*.'''

        # Build Unreal import task
        self.prepare_load_task(context_data, data, options)

        # Fbx geo specific options
        self.task.options = unreal.FbxImportUI()
        self.task.options.import_mesh = True
        self.task.options.import_as_skeletal = False
        self.task.options.import_materials = options.get(
            'ImportMaterials', False
        )
        self.task.options.import_animations = False
        self.task.options.create_physics_asset = options.get(
            'CreatePhysicsAsset', False
        )
        self.task.options.override_full_name = options.get(
            'OverrideFullName', True
        )
        self.task.options.automated_import_should_detect_type = options.get(
            'AutomatedImportShouldDetectType', False
        )
        self.task.options.mesh_type_to_import = (
            unreal.FBXImportType.FBXIT_STATIC_MESH
        )
        self.task.options.static_mesh_import_data = (
            unreal.FbxStaticMeshImportData()
        )
        self.task.options.static_mesh_import_data.set_editor_property(
            'combine_meshes', options.get('CombineMeshes', True)
        )

        results = {
            self.component_path: self.import_geometry(
                rename_mesh=options.get('RenameMesh', False),
                rename_mesh_prefix=options.get('RenameMeshPrefix', 'S_'),
            )
        }

        return results


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return

    fbx_geo_importer = UnrealFbxGeometryLoaderImporterPlugin(api_object)
    fbx_geo_importer.register()
