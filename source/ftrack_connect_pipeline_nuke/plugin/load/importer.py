# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

from ftrack_connect_pipeline import plugin
from ftrack_connect_pipeline_qt import plugin as pluginWidget
from ftrack_connect_pipeline_nuke.plugin import (
    BaseNukePlugin, BaseNukePluginWidget
)

from ftrack_connect_pipeline_nuke.utils import ftrack_asset_node
from ftrack_connect_pipeline_nuke.constants import asset as asset_const


class LoaderImporterNukePlugin(plugin.LoaderImporterPlugin, BaseNukePlugin):
    ''' Class representing a Collector Plugin

    .. note::

        _required_output a List
    '''
    asset_node_type = ftrack_asset_node.FtrackAssetTab

    def _run(self, event):
        '''

        ..Note:: There is diferent types of components to load on nuke. If we
        open a nuke scene, we don't add any ftrackTab.
        If we import a nuke scene, we don't add any FtrackTab for now.
        If we load a sequence or any other component as an alembic for example,
        we create an ftracktab to that resultant component nuke node.
        '''

        context = event['data']['settings']['context']
        self.logger.debug('Current context : {}'.format(context))

        data = event['data']['settings']['data']
        self.logger.debug('Current data : {}'.format(data))

        options = event['data']['settings']['options']

        super_result = super(LoaderImporterNukePlugin, self)._run(event)

        asset_load_mode = options.get('load_mode')

        if asset_load_mode == asset_const.OPEN_MODE:
            return super_result

        ftrack_node_class = self.get_asset_node(context, data, options)

        result = super_result.get('result')
        if result:
            scene_node = result.get(
                ftrack_node_class.asset_info[asset_const.COMPONENT_PATH]
            )

            ftrack_node = ftrack_node_class.init_tab(scene_node)

        return super_result


class LoaderImporterNukeWidget(pluginWidget.LoaderImporterWidget, BaseNukePluginWidget):
    ''' Class representing a Collector Widget

    .. note::

        _required_output a List
    '''

