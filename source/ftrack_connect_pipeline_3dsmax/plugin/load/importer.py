# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

from ftrack_connect_pipeline import plugin
from ftrack_connect_pipeline_qt import plugin as pluginWidget
from ftrack_connect_pipeline_3dsmax.plugin import (
    BaseMaxPlugin, BaseMaxPluginWidget
)

from ftrack_connect_pipeline.constants.asset import v2
from ftrack_connect_pipeline import asset
from ftrack_connect_pipeline.asset import asset_info
from ftrack_connect_pipeline_3dsmax.utils import custom_commands as max_utils
from ftrack_connect_pipeline_3dsmax.utils import max_alembic_commands as abc_utils
from ftrack_connect_pipeline_3dsmax.utils import ftrack_asset_node
from ftrack_connect_pipeline_3dsmax import constants


class LoaderImporterMaxPlugin(plugin.LoaderImporterPlugin, BaseMaxPlugin):
    ''' Class representing a Collector Plugin

    .. note::

        _required_output a List
    '''
    asset_node_type = ftrack_asset_node.FtrackAssetNode

    def _run(self, event):
        self.old_data = max_utils.get_current_scene_objects()
        self.logger.debug('Got current objects from scene')

        context = event['data']['settings']['context']
        self.logger.debug('Current context : {}'.format(context))

        data = event['data']['settings']['data']
        self.logger.debug('Current data : {}'.format(data))

        options = event['data']['settings']['options']
        self.logger.debug('Current options : {}'.format(options))

        super_result = super(LoaderImporterMaxPlugin, self)._run(event)

        # if options.get('component_name') == 'cache':
        #     options['alembic_import_args'] = abc_utils.get_str_options(
        #         options
        #     )
        # self.logger.debug('Alembic import options added')

        # TODO: Temp. remove this once options ticket is in place, this has to
        #  be assigned from the ui
        options['load_mode'] = 'import'

        asset_load_mode = options.get('load_mode')

        if asset_load_mode and asset_load_mode == constants.OPEN_MODE:
            return super_result

        self.new_data = max_utils.get_current_scene_objects()
        self.logger.debug(
            'Got all the objects in the scene after import'
        )

        self.link_to_ftrack_node(context, data, options)

        return super_result


    def link_to_ftrack_node(self, context, data, options):
        diff = self.new_data.difference(self.old_data)

        if not diff:
            self.logger.debug('No differences found in the scene')
            return

        self.logger.debug(
            'Checked differences between nodes before and after'
            ' inport : {}'.format(diff)
        )

        ftrack_node_class = self.get_asset_node(context, data, options)

        ftrack_node = ftrack_node_class.init_node()

        ftrack_node_class.connect_objects(diff)


class ImporterMaxWidget(pluginWidget.LoaderImporterWidget, BaseMaxPluginWidget):
    ''' Class representing a Collector Widget

    .. note::

        _required_output a List
    '''

