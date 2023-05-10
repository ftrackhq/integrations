# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import unreal

import ftrack_api

from ftrack_connect_pipeline_unreal import plugin
from ftrack_connect_pipeline_unreal.constants.asset import modes as load_const


class UnrealFbxAnimationLoaderImporterPlugin(
    plugin.UnrealLoaderImporterPlugin
):
    load_modes = load_const.LOAD_MODES

    plugin_name = 'unreal_fbx_animation_loader_importer'

    def run(self, context_data=None, data=None, options=None):
        '''Load FBX animation file pointed out by collected *data*, with *options*.'''

        # Build Unreal import task
        self.prepare_load_task(context_data, data, options)

        # Fbx animation specific options
        self.task.options = unreal.FbxImportUI()
        self.task.options.import_mesh = False
        self.task.options.import_as_skeletal = False
        self.task.options.import_animations = True
        self.task.options.import_materials = options.get(
            'ImportMaterials', False
        )
        self.task.options.create_physics_asset = False
        self.task.options.automated_import_should_detect_type = False
        self.task.options.mesh_type_to_import = (
            unreal.FBXImportType.FBXIT_ANIMATION
        )
        self.task.options.anim_sequence_import_data = (
            unreal.FbxAnimSequenceImportData()
        )

        self.task.options.anim_sequence_import_data.set_editor_property(
            'import_bone_tracks', options.get('ImportBoneTracks', True)
        )
        self.task.options.anim_sequence_import_data.set_editor_property(
            'import_custom_attribute',
            options.get('ImportCustomAttribute', True),
        )

        if options.get('UseCustomRange', True):
            self.task.options.anim_sequence_import_data.set_editor_property(
                'animation_length',
                unreal.FBXAnimationLengthImportType.FBXALIT_SET_RANGE,
            )
            range_interval = unreal.Int32Interval()
            range_interval.set_editor_property('min', options['AnimRangeMin'])
            range_interval.set_editor_property('max', options['AnimRangeMax'])
            self.task.options.anim_sequence_import_data.set_editor_property(
                'frame_import_range', range_interval
            )
        else:
            self.task.options.anim_sequence_import_data.set_editor_property(
                'animation_length',
                unreal.FBXAnimationLengthImportType.FBXALIT_EXPORTED_TIME,
            )

        results = {
            self.component_path: self.import_animation(
                skeleton_name=options.get('Skeleton'),
                rename_animation=options.get('RenameAnimation', False),
                rename_animation_prefix=options.get(
                    'RenameAnimationPrefix', 'A_'
                ),
            )
        }

        return results


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return

    fbx_geo_importer = UnrealFbxAnimationLoaderImporterPlugin(api_object)
    fbx_geo_importer.register()
