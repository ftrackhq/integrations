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
        task, component_path = super(
            UnrealFbxAnimationLoaderImporterPlugin, self
        ).run(context_data, data, options)

        # Fbx animation specific options
        task.options = unreal.FbxImportUI()
        task.options.import_mesh = False
        task.options.import_as_skeletal = False
        task.options.import_animations = True
        task.options.import_materials = options.get('ImportMaterials', False)
        task.options.create_physics_asset = False
        task.options.automated_import_should_detect_type = False
        task.options.mesh_type_to_import = unreal.FBXImportType.FBXIT_ANIMATION
        task.options.anim_sequence_import_data = (
            unreal.FbxAnimSequenceImportData()
        )

        task.options.anim_sequence_import_data.set_editor_property(
            'import_bone_tracks', options.get('ImportBoneTracks', True)
        )
        task.options.anim_sequence_import_data.set_editor_property(
            'import_custom_attribute',
            options.get('ImportCustomAttribute', True),
        )

        if options.get('UseCustomRange', True):
            task.options.anim_sequence_import_data.set_editor_property(
                'animation_length',
                unreal.FBXAnimationLengthImportType.FBXALIT_SET_RANGE,
            )
            range_interval = unreal.Int32Interval()
            range_interval.set_editor_property('min', options['AnimRangeMin'])
            range_interval.set_editor_property('max', options['AnimRangeMax'])
            task.options.anim_sequence_import_data.set_editor_property(
                'frame_import_range', range_interval
            )
        else:
            task.options.anim_sequence_import_data.set_editor_property(
                'animation_length',
                unreal.FBXAnimationLengthImportType.FBXALIT_EXPORTED_TIME,
            )

        return self.import_animation(task, component_path, options)


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return

    fbx_geo_importer = UnrealFbxAnimationLoaderImporterPlugin(api_object)
    fbx_geo_importer.register()
