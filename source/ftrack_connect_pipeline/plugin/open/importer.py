# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

import json
import six
import base64

from ftrack_connect_pipeline import constants
from ftrack_connect_pipeline.plugin import base
from ftrack_connect_pipeline.asset import asset_info as ainfo
from ftrack_connect_pipeline.constants import asset as asset_const


class OpenerImporterPlugin(base.BaseImporterPlugin):
    '''
    Base Opener Importer Plugin Class inherits from
    :class:`~ftrack_connect_pipeline.plugin.base.BaseImporterPlugin`
    '''

    return_type = dict
    '''Required return type'''
    plugin_type = constants.PLUGIN_OPENER_IMPORTER_TYPE
    '''Type of the plugin'''
    _required_output = {}
    '''Required return output'''

    open_modes = {}
    '''Available open modes for an asset'''

    dependency_open_mode = ''
    '''Default defendency open Mode'''

    json_data = {}
    '''Extra json data with the current open options'''

    def __init__(self, session):
        super(OpenerImporterPlugin, self).__init__(session)
        self.ftrack_asset = None

    def _parse_run_event(self, event):
        '''
        Parse the event given on the :meth:`_run`. Returns method name to be
        executed and plugin_setting to be passed to the method.
        This is an override that modifies the plugin_setting['data'] to pass
        only the results of the collector stage of the current step.
        '''
        method, plugin_settings = super(
            OpenerImporterPlugin, self
        )._parse_run_event(event)
        data = plugin_settings.get('data')
        # We only want the data of the collector in this stage
        collector_result = []
        component_step = data[-1]
        if component_step.get('category') == 'plugin':
            return method, plugin_settings
        for component_stage in component_step.get("result"):
            if component_stage.get("name") == constants.COLLECTOR:
                collector_result = component_stage.get("result")
                break
        if collector_result:
            plugin_settings['data'] = collector_result
        return method, plugin_settings

    def get_current_objects(self):
        # TODO: implement this function on the dcc plugin importer.py
        raise NotImplementedError

    def init_nodes(self, context_data=None, data=None, options=None):
        '''Alternative plugin method to init all the nodes in the scene but not
        need to open the assets'''
        if six.PY2:
            options[asset_const.ASSET_INFO_OPTIONS] = base64.b64encode(
                self.json_data
            )
        else:
            input_bytes = self.json_data.encode('utf8')
            options[asset_const.ASSET_INFO_OPTIONS] = base64.b64encode(
                input_bytes
            ).decode('ascii')

        arguments_dict = ainfo.generate_asset_info_dict_from_args(
            context_data, data, options, self.session
        )

        asset_info = ainfo.FtrackAssetInfo(arguments_dict)

        self.ftrack_asset = self.ftrack_asset_class(self.event_manager)
        self.ftrack_asset.set_asset_info(asset_info)

        ftrack_object = self.ftrack_asset.init_ftrack_object(
            create_object=True, is_opened=False
        )

        results = [ftrack_object]
        return results

    def open_asset(self, context_data=None, data=None, options=None):
        '''Alternative plugin method to only open the asset in the scene'''

        self.ftrack_asset = self.ftrack_asset_class(self.event_manager)
        asset_info = options.get('asset_info')
        self.ftrack_asset.set_asset_info(asset_info)
        self.ftrack_asset.init_ftrack_object(
            create_object=False, is_opened=True
        )
        # Remove asset_info from the options as it is not needed anymore
        options.pop('asset_info')
        # Execute the run method to open the objects
        self.run(context_data, data, options)
        #  Query all the objects from the scene
        self.new_data = self.get_current_objects()
        self.logger.debug(
            'Scene objects after open : {}'.format(len(self.new_data))
        )
        diff = self.new_data.difference(self.old_data)

        # Connect scene objects to ftrack node
        self.ftrack_asset.connect_objects(diff)

    def init_and_open(self, context_data=None, data=None, options=None):
        '''Alternative plugin method to init and open the node and the assets
        into the scene'''

        self.init_nodes(context_data=context_data, data=data, options=options)
        options['asset_info'] = self.ftrack_asset.asset_info
        self.open_asset(context_data=context_data, data=data, options=options)

    def _run(self, event):
        self.old_data = self.get_current_objects()
        self.logger.debug('Current objects : {}'.format(len(self.old_data)))
        # Having this in a separate method, we can override the parse depending
        #  on the plugin type.
        self._method, self._plugin_settings = self._parse_run_event(event)

        context_data = self.plugin_settings.get('context_data')
        self.logger.debug('Current context : {}'.format(context_data))

        data = self.plugin_settings.get('data')
        self.logger.debug('Current data : {}'.format(data))

        options = self.plugin_settings.get('options')
        self.logger.debug('Current options : {}'.format(options))

        # set non serializable keys like "session" to not serializable, used in
        # case data contains the asset info from the scene
        self.json_data = json.dumps(
            event['data'], default=lambda o: '<not serializable>'
        )

        super_result = super(OpenerImporterPlugin, self)._run(event)

        return super_result
