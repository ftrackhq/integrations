# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import json

from ftrack_connect_pipeline import plugin
from ftrack_connect_pipeline_qt import plugin as pluginWidget
from ftrack_connect_pipeline_nuke.plugin import (
    BaseNukePlugin, BaseNukePluginWidget
)

from ftrack_connect_pipeline_nuke.asset import FtrackAssetTab
from ftrack_connect_pipeline_nuke.constants import asset as asset_const
from ftrack_connect_pipeline_nuke.constants.asset import modes as load_const
from ftrack_connect_pipeline_nuke.utils import custom_commands as nuke_utils


class LoaderImporterNukePlugin(plugin.LoaderImporterPlugin, BaseNukePlugin):
    ''' Class representing a Collector Plugin

    .. note::

        _required_output a List
    '''
    asset_node_type = FtrackAssetTab

    def _run(self, event):
        '''

        ..Note:: There is diferent types of components to load on nuke. If we
        open a nuke scene, we don't add any ftrackTab.
        If we import a nuke scene, we don't add any FtrackTab for now.
        If we load a sequence or any other component as an alembic for example,
        we create an ftracktab to that resultant component nuke ftrack_object.
        '''
        self.old_data = nuke_utils.get_current_scene_objects()
        self.logger.debug('Scene objects : {}'.format(len(self.old_data)))

        context = event['data']['settings']['context']
        self.logger.debug('Current context : {}'.format(context))

        data = event['data']['settings']['data']
        self.logger.debug('Current data : {}'.format(data))

        options = event['data']['settings']['options']

        super_result = super(LoaderImporterNukePlugin, self)._run(event)

        options[asset_const.ASSET_INFO_OPTIONS] = json.dumps(
            event['data']
        ).encode('base64')

        asset_load_mode = options.get(asset_const.LOAD_MODE)

        if asset_load_mode == load_const.OPEN_MODE:
            return super_result

        self.new_data = nuke_utils.get_current_scene_objects()

        diff = self.new_data.difference(self.old_data)

        if not diff:
            self.logger.debug('No differences found in the scene')
            return

        self.logger.debug(
            'Checked differences between ftrack_objects before and after'
            ' inport : {}'.format(diff)
        )

        ftrack_node_class = self.get_asset_node(context, data, options)

        result = super_result.get('result')

        if asset_load_mode == load_const.REFERENCE_MODE:
            if result:
                scene_node = result.get(
                            ftrack_node_class.asset_info[
                                asset_const.COMPONENT_PATH
                            ]
                        )
                ftrack_node_class.set_ftrack_object(ftrack_object=scene_node)
        else:
            ftrack_node_class.set_ftrack_object()

        ftrack_node = ftrack_node_class.init_ftrack_object()

        ftrack_node_class.connect_objects(diff)


        return super_result


class LoaderImporterNukeWidget(pluginWidget.LoaderImporterWidget, BaseNukePluginWidget):
    ''' Class representing a Collector Widget

    .. note::

        _required_output a List
    '''

