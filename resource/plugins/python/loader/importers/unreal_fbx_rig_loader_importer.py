# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import unreal

import ftrack_api

from ftrack_connect_pipeline_unreal import plugin
from ftrack_connect_pipeline_unreal.constants.asset import modes as load_const
from ftrack_connect_pipeline_unreal.utils import (
    misc as unreal_misc_utils,
    node as unreal_node_utils,
    file as unreal_file_utils,
)


class UnrealFbxRigLoaderImporterPlugin(plugin.UnrealLoaderImporterPlugin):
    load_modes = load_const.LOAD_MODES

    plugin_name = 'unreal_fbx_rig_loader_importer'

    def run(self, context_data=None, data=None, options=None):
        '''Load FBX rig file pointed out by collected *data*, with *options*.'''

        # Build import task
        task, component_path = unreal_misc_utils.prepare_load_task(
            self.session, context_data, data, options
        )

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

        # Rig specific options
        skeleton_name = options.get('Skeleton')
        if skeleton_name:
            skeletons = unreal_node_utils.get_asset_by_class('Skeleton')
            skeleton_ad = None
            for skeleton in skeletons:
                if skeleton.asset_name == skeleton_name:
                    skeleton_ad = skeleton

            if skeleton_ad is not None:
                task.options.set_editor_property(
                    'skeleton', skeleton_ad.get_asset()
                )

        import_result = unreal_file_utils.import_file(task)
        self.logger.info('Imported FBX rig: {}'.format(import_result))
        loaded_skeletal_mesh = unreal.EditorAssetLibrary.load_asset(
            import_result
        )

        results = {component_path: []}

        if options.get('RenameSkelMesh', False):
            results[component_path].append(
                unreal_misc_utils.rename_node_with_prefix(
                    import_result, options.get('RenameSkelMeshPrefix', 'SK_')
                )
            )
        else:
            results[component_path].append(
                loaded_skeletal_mesh.get_path_name()
            )

        mesh_skeleton = loaded_skeletal_mesh.skeleton
        if mesh_skeleton:
            if options.get('RenameSkeleton', False):
                results[component_path].append(
                    unreal_misc_utils.rename_node_with_prefix(
                        mesh_skeleton.get_path_name(),
                        options.get('RenameSkeletonPrefix', 'SKEL_'),
                    )
                )
            else:
                results[component_path].append(mesh_skeleton.get_path_name())

        mesh_physics_asset = loaded_skeletal_mesh.physics_asset
        if mesh_physics_asset:
            if options.get('RenamePhysAsset', False):
                results[component_path].append(
                    unreal_misc_utils.rename_node_with_prefix(
                        mesh_physics_asset.get_path_name(),
                        options.get('RenamePhysAssetPrefix', 'PHAT_'),
                    )
                )
            else:
                results[component_path].append(
                    mesh_physics_asset.get_path_name()
                )

        return results


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return

    fbx_geo_importer = UnrealFbxRigLoaderImporterPlugin(api_object)
    fbx_geo_importer.register()
