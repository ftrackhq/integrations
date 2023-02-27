# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import unreal

import ftrack_api

from ftrack_connect_pipeline_unreal import plugin
from ftrack_connect_pipeline_unreal.constants.asset import modes as load_const
from ftrack_connect_pipeline_unreal import utils


class UnrealAbcAnimationLoaderImporterPlugin(
    plugin.UnrealAnimationLoaderImporterPlugin
):
    load_modes = load_const.LOAD_MODES

    plugin_name = 'unreal_abc_animation_loader_importer'

    def run(self, context_data=None, data=None, options=None):
        """Load Alembic animation file pointed out by collected *data*, with *options*."""

        # Build Unreal import task
        task, component_path = super(
            UnrealAbcAnimationLoaderImporterPlugin, self
        ).run(context_data, data, options)

        # Alembic animation specific options
        task.options = unreal.AbcImportSettings()
        task.options.import_type = unreal.AlembicImportType.GEOMETRY_CACHE
        task.options.material_settings.set_editor_property(
            'find_materials', options.get('ImportMaterials', False)
        )

        if options.get('UseCustomRange'):
            task.options.sampling_settings.frame_start = options[
                'AnimRangeMin'
            ]
            task.options.sampling_settings.frame_end = options['AnimRangeMax']

        return self.import_animation(task, component_path, options)


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return

    abc_geo_importer = UnrealAbcAnimationLoaderImporterPlugin(api_object)
    abc_geo_importer.register()
