# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import unreal

import ftrack_api

from ftrack_connect_pipeline_unreal import plugin
from ftrack_connect_pipeline_unreal.constants.asset import modes as load_const
from ftrack_connect_pipeline_unreal import utils


class UnrealFbxRigLoaderImporterPlugin(plugin.UnrealRigLoaderImporterPlugin):
    load_modes = load_const.LOAD_MODES

    plugin_name = 'unreal_fbx_rig_loader_importer'

    def run(self, context_data=None, data=None, options=None):
        '''Load FBX rig file pointed out by collected *data*, with *options*.'''

        # Build Unreal import task
        task, component_path = super(
            UnrealFbxRigLoaderImporterPlugin, self
        ).run(context_data, data, options)

        # Fbx rig specific options
        task.options = unreal.FbxImportUI()
        task.options.import_mesh = False
        task.options.import_as_skeletal = True
        task.options.import_animations = False
        task.options.import_materials = options.get('ImportMaterials', False)
        task.options.create_physics_asset = options.get(
            'CreatePhysicsAsset', True
        )
        task.options.automated_import_should_detect_type = options.get(
            'AutomatedImportShouldDetectType', False
        )
        task.options.mesh_type_to_import = (
            unreal.FBXImportType.FBXIT_SKELETAL_MESH
        )
        task.options.skeletal_mesh_import_data = (
            unreal.FbxSkeletalMeshImportData()
        )
        task.options.skeletal_mesh_import_data.normal_import_method = (
            unreal.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS_AND_TANGENTS
        )
        task.options.skeletal_mesh_import_data.set_editor_property(
            'import_morph_targets', options.get('ImportMorphTargets', True)
        )

        return self.import_rig(task, component_path, options)


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return

    fbx_geo_importer = UnrealFbxRigLoaderImporterPlugin(api_object)
    fbx_geo_importer.register()
