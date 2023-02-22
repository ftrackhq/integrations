# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

import unreal

from ftrack_connect_pipeline_unreal import plugin
from ftrack_connect_pipeline_unreal.constants.asset import modes as load_const
from ftrack_connect_pipeline_unreal.utils import (
    misc as unreal_misc_utils,
    file as unreal_file_utils,
)
import ftrack_api


class UnrealAbcGeometryLoaderImporterPlugin(plugin.UnrealLoaderImporterPlugin):
    load_modes = load_const.LOAD_MODES

    plugin_name = 'unreal_abc_geometry_loader_importer'

    def run(self, context_data=None, data=None, options=None):
        """Load Alembic geometry file pointed out by collected *data*, with *options*."""

        # Build import task
        task, component_path = unreal_misc_utils.prepare_load_task(
            self.session, context_data, data, options
        )

        # Alembic geo specific options
        task.options = unreal.AbcImportSettings()
        task.options.import_type = unreal.AlembicImportType.STATIC_MESH
        task.options.material_settings.set_editor_property(
            'find_materials', options.get('ImportMaterials', False)
        )

        # Geometry specific options
        import_result = unreal_file_utils.import_file(task)

        if import_result is None:
            raise Exception('Alembic geo import failed!')

        self.logger.info('Imported Alembic geo: {}'.format(import_result))

        results = {}

        if options.get('RenameMesh', False):
            results[
                component_path
            ] = unreal_misc_utils.rename_node_with_prefix(
                import_result, options.get('RenameMeshPrefix', 'S_')
            )

        return results


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return

    abc_geo_importer = UnrealAbcGeometryLoaderImporterPlugin(api_object)
    abc_geo_importer.register()
