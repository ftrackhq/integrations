# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack
from pymxs import runtime as rt

import ftrack_api

from ftrack_connect_pipeline_3dsmax import plugin
from ftrack_connect_pipeline_3dsmax.constants.asset import modes as load_const
from ftrack_connect_pipeline_3dsmax.constants import asset as asset_const


class MaxAbcLoaderImporterPlugin(plugin.MaxLoaderImporterPlugin):
    plugin_name = 'max_abc_loader_importer'

    load_modes = load_const.LOAD_MODES

    def run(self, context_data=None, data=None, options=None):
        '''Import collected Alembic objects provided with *data* into Max based on *options*'''

        results = {}

        paths_to_import = []
        for collector in data:
            paths_to_import.append(
                collector['result'].get(asset_const.COMPONENT_PATH)
            )

        for component_path in paths_to_import:
            self.logger.debug('Loading alembic path {}'.format(component_path))

            try:
                for key, value in list(options.items()):
                    if key.startswith('ABC'):
                        key = key[3:]
                        self.logger.debug(
                            'Setting parameter {}: {}'.format(key, value)
                        )
                        try:
                            cmd = 'rt.AlembicImport.{}={}'.format(
                                key,
                                '{1}{0}{1}'.format(
                                    options[key],
                                    '"'
                                    if isinstance(options[key], str)
                                    else '',
                                ),
                            )
                            eval(cmd)
                        except Exception as e:
                            self.logger.exception(e)

                load_result = rt.importFile(
                    component_path, rt.name("noPrompt"), using="AlembicImport"
                )

            except RuntimeError as e:
                return False, {'message': self.logger.error(str(e))}

            results[component_path] = load_result

        return results


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = MaxAbcLoaderImporterPlugin(api_object)
    plugin.register()
