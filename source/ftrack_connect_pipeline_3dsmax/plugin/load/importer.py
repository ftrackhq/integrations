# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

from ftrack_connect_pipeline import plugin
from ftrack_connect_pipeline_qt import plugin as pluginWidget
from ftrack_connect_pipeline_3dsmax.plugin import (
    BaseMaxPlugin, BaseMaxPluginWidget
)

from ftrack_connect_pipeline_3dsmax.utils import custom_commands as max_utils
from ftrack_connect_pipeline_3dsmax.utils import max_alembic_commands as abc_utils
from ftrack_connect_pipeline_3dsmax.utils import ftrack_asset_node
from ftrack_connect_pipeline_3dsmax import constants


class LoaderImporterMaxPlugin(plugin.LoaderImporterPlugin, BaseMaxPlugin):
    ''' Class representing a Collector Plugin

    .. note::

        _required_output a List
    '''

    def _run(self, event):
        self.old_data = max_utils.get_current_scene_objects()
        self.logger.debug('Got current objects from scene')

        context = event['data']['settings']['context']
        self.logger.debug('Current context : {}'.format(context))

        data = event['data']['settings']['data']
        self.logger.debug('Current data : {}'.format(data))

        options = event['data']['settings']['options']
        self.logger.debug('Current data : {}'.format(data))

        self.logger.debug('Running the base _run function')
        super_result = super(LoaderImporterMaxPlugin, self)._run(event)

        self.logger.debug(
            'Assigning the processed string alembic import arguments to add to '
            'ftrack node'
        )
        options['alembic_import_args'] = abc_utils.get_str_options(
            options
        )

        # TODO: Temp. remove this once options is filled
        options['load_mode'] = 'import'
        #TODO: this has to come from the ui and has to be set to none in case
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

        #TODo: Remove self.session argument as will not be needed when the
        # FtrackAssetNode class is part of the core pipeline
        ftrack_node_class = ftrack_asset_node.FtrackAssetNode(
            context, data, options, self.session
        )
        ftrack_node = ftrack_node_class.init_ftrack_node()

        ftrack_node_class.connect_objects_to_ftrack_node(diff)


class ImporterMaxWidget(pluginWidget.LoaderImporterWidget, BaseMaxPluginWidget):
    ''' Class representing a Collector Widget

    .. note::

        _required_output a List
    '''

