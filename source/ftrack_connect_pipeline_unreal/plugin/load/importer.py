# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import os
import unreal

from ftrack_connect_pipeline import plugin

from ftrack_connect_pipeline_qt import plugin as pluginWidget

from ftrack_connect_pipeline_unreal.plugin import (
    UnrealBasePlugin,
    UnrealBasePluginWidget,
)
from ftrack_connect_pipeline_unreal import utils
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

    @utils.run_in_main_thread
    def get_current_objects(self):
        return utils.get_current_scene_objects()

    def prepare_load_task(self, context_data, data, options):
        '''Prepare loader import task based on *data* and *context_data*, using *options*.'''

        paths_to_import = []
        for collector in data:
            paths_to_import.append(
                collector['result'].get(asset_const.COMPONENT_PATH)
            )

        self.component_path = paths_to_import[0]

        # Check if it exists
        if not os.path.exists(self.component_path):
            raise Exception(
                'The asset file does not exist: "{}"'.format(self.component_path)
            )

        self.task = unreal.AssetImportTask()

        self.task.filename = self.component_path

        # Determine the folder to import to
        selected_context_browser_path = (
            unreal.EditorUtilityLibrary.get_current_content_browser_path()
        )
        if selected_context_browser_path is not None:
            import_path = selected_context_browser_path
        else:
            import_path = '/Game'

        self.task.destination_path = import_path.replace(' ', '_')
        destination_name_base = context_data['asset_name'].replace(' ', '_')

        # Make sure we do not everwrite any existing asset
        n = 1
        while True:
            destination_name = '{}{}'.format(
                destination_name_base, '_{}'.format(n) if n > 1 else ''
            )
            path = utils.asset_path_to_filesystem_path(
                '{}/{}'.format(self.task.destination_path, destination_name),
                throw_on_error=False,
            )
            if path is None:
                break
            n += 1
        self.task.destination_name = destination_name

        self.task.replace_existing = options.get('ReplaceExisting', True)
        self.task.automated = options.get('Automated', True)
        self.task.save = options.get('Save', True)

    def import_geometry(self, task, component_path, options):
        '''
        Geometry import from prepared *task*, *component_path* with *options*.
        '''
        import_result = utils.import_file(task)
        if import_result is None:
            raise Exception('Geometry import failed!')
        self.logger.info('Imported geometry: {}'.format(import_result))

        import_result = None

        if options.get('RenameMesh', False):
            import_result = utils.rename_node_with_prefix(
                import_result, options.get('RenameMeshPrefix', 'S_')
            )
        else:
            import_result = import_result

        return import_result


    def import_rig(self, options):
        '''
        Rig import from prepared *task*, *component_path* with *options*.
        '''
        # Rig specific options
        skeleton_name = options.get('Skeleton')
        if skeleton_name:
            skeletons = utils.get_assets_by_class('Skeleton')
            skeleton_ad = None
            for skeleton in skeletons:
                if skeleton.asset_name == skeleton_name:
                    skeleton_ad = skeleton

            if skeleton_ad is not None:
                self.task.options.set_editor_property(
                    'skeleton', skeleton_ad.get_asset()
                )

        import_result = utils.import_file(self.task)
        self.logger.info('Imported rig: {}'.format(import_result))
        loaded_skeletal_mesh = unreal.EditorAssetLibrary.load_asset(
            import_result
        )

        import_result = []

        results = {self.component_path: []}

        if options.get('RenameSkelMesh', False):
            results[self.component_path].append(
                utils.rename_node_with_prefix(
                    import_result, options.get('RenameSkelMeshPrefix', 'SK_')
                )
            )
        else:
            results[self.component_path].append(
                loaded_skeletal_mesh.get_path_name()
            )

        mesh_skeleton = loaded_skeletal_mesh.skeleton
        if mesh_skeleton:
            if options.get('RenameSkeleton', False):
                results[self.component_path].append(
                    utils.rename_node_with_prefix(
                        mesh_skeleton.get_path_name(),
                        options.get('RenameSkeletonPrefix', 'SKEL_'),
                    )
                )
            else:
                results[self.component_path].append(mesh_skeleton.get_path_name())

        mesh_physics_asset = loaded_skeletal_mesh.physics_asset
        if mesh_physics_asset:
            if options.get('RenamePhysAsset', False):
                results[self.component_path].append(
                    utils.rename_node_with_prefix(
                        mesh_physics_asset.get_path_name(),
                        options.get('RenamePhysAssetPrefix', 'PHAT_'),
                    )
                )
            else:
                results[self.component_path].append(
                    mesh_physics_asset.get_path_name()
                )

        return results


    def import_animation(self, options):
        '''
        Animation import from prepared *task*, *component_path* with *options*.
        '''
        skeleton_name = options.get('Skeleton')
        if skeleton_name:
            skeletons = utils.get_assets_by_class('Skeleton')
            skeleton_ad = None
            for skeleton in skeletons:
                if skeleton.asset_name == skeleton_name:
                    skeleton_ad = skeleton

            if skeleton_ad is not None:
                self.task.options.set_editor_property(
                    'skeleton', skeleton_ad.get_asset()
                )

        import_result = utils.import_file(self.task)
        self.logger.info('Imported animation: {}'.format(import_result))

        results = {}

        if options.get('RenameAnim', False):
            results[self.component_path] = utils.rename_node_with_prefix(
                import_result, options.get('RenameAnimPrefix', 'A_')
            )
        else:
            results[self.component_path] = import_result

        return results



class UnrealLoaderImporterPluginWidget(
    pluginWidget.LoaderImporterPluginWidget, UnrealBasePluginWidget
):
    '''Class representing a Collector Widget

    .. note::

        _required_output a List
    '''
