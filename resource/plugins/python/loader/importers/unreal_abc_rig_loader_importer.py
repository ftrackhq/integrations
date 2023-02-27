# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import unreal

import ftrack_api

from ftrack_connect_pipeline_unreal import plugin
from ftrack_connect_pipeline_unreal.constants.asset import modes as load_const
from ftrack_connect_pipeline_unreal import utils


class UnrealAbcRigLoaderImporterPlugin(plugin.UnrealRigLoaderImporterPlugin):
    load_modes = load_const.LOAD_MODES

    plugin_name = 'unreal_abc_rig_loader_importer'

    def run(self, context_data=None, data=None, options=None):
        '''Load Alembic rig file pointed out by collected *data*, with *options*.'''

        # Build Unreal import task
        task, component_path = super(
            UnrealAbcRigLoaderImporterPlugin, self
        ).run(context_data, data, options)

        # Alembic rig specific options
        task.options = unreal.AbcImportSettings()
        task.options.import_type = unreal.AlembicImportType.SKELETAL
        task.options.material_settings.set_editor_property(
            'find_materials', options.get('ImportMaterials', False)
        )

        return self.import_rig(task, component_path, options)


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return

    abc_geo_importer = UnrealAbcRigLoaderImporterPlugin(api_object)
    abc_geo_importer.register()
