# :coding: utf-8
# :copyright: Copyright (c) 2014-2021 ftrack

import json
import base64

from ftrack_connect_pipeline import plugin
from ftrack_connect_pipeline_qt import plugin as pluginWidget
from ftrack_connect_pipeline_houdini.plugin import (
    BaseHoudiniPlugin, BaseHoudiniPluginWidget
)

from ftrack_connect_pipeline_houdini.asset import FtrackAssetTab
from ftrack_connect_pipeline_houdini.constants import asset as asset_const
from ftrack_connect_pipeline_houdini.constants.asset import modes as load_const
from ftrack_connect_pipeline_houdini.utils import custom_commands as houdini_utils


class LoaderImporterHoudiniPlugin(plugin.LoaderImporterPlugin,
                                  BaseHoudiniPlugin):
    ''' Class representing a Collector Plugin

    .. note::

        _required_output a List
    '''
    ftrack_asset_class = FtrackAssetTab

    def _run(self, event):
        '''

        If we import a houdini scene, we don't add any FtrackTab for now.

        '''

        try:
            #self.old_data = houdini_utils.get_current_scene_objects()
            #self.logger.info('Scene objects : {}'.format(len(self.old_data)))

            super_result = super(LoaderImporterHoudiniPlugin, self)._run(event)

            context = self.plugin_settings.get('context')
            self.logger.debug('Current context : {}'.format(context))

            data = self.plugin_settings.get('data')
            self.logger.debug('Current data : {}'.format(data))

            options = self.plugin_settings.get('options')
            self.logger.debug('Current options: {}'.format(options))

            options[asset_const.ASSET_INFO_OPTIONS] = base64.encodebytes(
                json.dumps(event['data']).encode('utf-8')
            ).decode('utf-8')

            asset_load_mode = options.get(asset_const.LOAD_MODE)

            if asset_load_mode != load_const.OPEN_MODE and asset_load_mode != \
                    load_const.MERGE_MODE:

                result = super_result.get('result',{})

                if isinstance(result, dict):
                    run = result.get('run')
                    if isinstance(run, dict):
                        # Import was successful, store ftrack metadata
                        ftrack_asset_class = self.get_asset_class(context, data,
                                                                  options)

                        # Only one component expected
                        for (path_component, obj_path_or_paths) in run.items():
                            # Can arrive as a single or multiple object paths
                            ftrack_asset_class.connect_objects(obj_path_or_paths
                            if isinstance(obj_path_or_paths, list) else
                            [obj_path_or_paths])

            return super_result

        except:
            import traceback
            self.logger.error(traceback.format_exc())
            raise


class LoaderImporterHoudiniWidget(pluginWidget.LoaderImporterWidget,
                                  BaseHoudiniPluginWidget):
    ''' Class representing a Collector Widget

    .. note::

        _required_output a List
    '''

