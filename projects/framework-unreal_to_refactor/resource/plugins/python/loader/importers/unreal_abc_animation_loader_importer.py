# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import unreal

import ftrack_api

from ftrack_framework_unreal import plugin
from ftrack_framework_unreal.constants.asset import modes as load_const


class UnrealAbcAnimationLoaderImporterPlugin(
    plugin.UnrealLoaderImporterPlugin
):
    load_modes = load_const.LOAD_MODES

    plugin_name = 'unreal_abc_animation_loader_importer'

    def run(self, context_data=None, data=None, options=None):
        '''Load Alembic animation file pointed out by collected *data*, with *options*.'''

        # Build Unreal import task
        self.prepare_load_task(context_data, data, options)

        # Alembic animation specific options
        self.task.options = unreal.AbcImportSettings()
        self.task.options.import_type = unreal.AlembicImportType.GEOMETRY_CACHE
        self.task.options.material_settings.set_editor_property(
            'find_materials', options.get('ImportMaterials', False)
        )

        if options.get('UseCustomRange'):
            self.task.options.sampling_settings.frame_start = options[
                'AnimRangeMin'
            ]
            self.task.options.sampling_settings.frame_end = options[
                'AnimRangeMax'
            ]

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

    abc_geo_importer = UnrealAbcAnimationLoaderImporterPlugin(api_object)
    abc_geo_importer.register()
