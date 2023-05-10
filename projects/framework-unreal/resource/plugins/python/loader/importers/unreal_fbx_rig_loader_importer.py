# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import unreal

import ftrack_api

from ftrack_connect_pipeline_unreal import plugin
from ftrack_connect_pipeline_unreal.constants.asset import modes as load_const


class UnrealFbxRigLoaderImporterPlugin(plugin.UnrealLoaderImporterPlugin):
    load_modes = load_const.LOAD_MODES

    plugin_name = 'unreal_fbx_rig_loader_importer'

    def run(self, context_data=None, data=None, options=None):
        '''Load FBX rig file pointed out by collected *data*, with *options*.'''

        # Build Unreal import task
        self.prepare_load_task(context_data, data, options)

        # Fbx rig specific options
        self.task.options = unreal.FbxImportUI()
        self.task.options.import_mesh = False
        self.task.options.import_as_skeletal = True
        self.task.options.import_animations = False
        self.task.options.import_materials = options.get(
            'ImportMaterials', False
        )
        self.task.options.create_physics_asset = options.get(
            'CreatePhysicsAsset', True
        )
        self.task.options.automated_import_should_detect_type = options.get(
            'AutomatedImportShouldDetectType', False
        )
        self.task.options.mesh_type_to_import = (
            unreal.FBXImportType.FBXIT_SKELETAL_MESH
        )
        self.task.options.skeletal_mesh_import_data = (
            unreal.FbxSkeletalMeshImportData()
        )
        self.task.options.skeletal_mesh_import_data.normal_import_method = (
            unreal.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS_AND_TANGENTS
        )
        self.task.options.skeletal_mesh_import_data.set_editor_property(
            'import_morph_targets', options.get('ImportMorphTargets', True)
        )

        results = {
            self.component_path: self.import_rig(
                skeleton_name=options.get('Skeleton'),
                rename_skeleton_mesh=options.get('RenameSkeletonMesh', False),
                rename_skeleton_mesh_prefix=options.get(
                    'RenameSkeletonMeshPrefix', 'SK_'
                ),
                rename_skeleton=options.get('RenameSkeleton', False),
                rename_skeleton_prefix=options.get(
                    'RenameSkeletonPrefix', 'SKEL_'
                ),
                rename_physics_asset=options.get('RenamePhysicsAsset', False),
                rename_physics_asset_prefix=options.get(
                    'RenamePhysicsAssetPrefix', 'PHAT_'
                ),
            )
        }

        return results


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return

    fbx_geo_importer = UnrealFbxRigLoaderImporterPlugin(api_object)
    fbx_geo_importer.register()
