# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

import json
import six
import base64

from ftrack_connect_pipeline import constants
from ftrack_connect_pipeline.plugin import base
from ftrack_connect_pipeline.constants import asset as asset_const


class LoaderImporterPlugin(base.BaseImporterPlugin):
    '''
    Base Loader Importer Plugin Class inherits from
    :class:`~ftrack_connect_pipeline.plugin.base.BaseImporterPlugin`
    '''
    return_type = dict
    '''Required return type'''
    plugin_type = constants.PLUGIN_LOADER_IMPORTER_TYPE
    '''Type of the plugin'''
    _required_output = {}
    '''Required return output'''

    load_modes = {}
    '''Available load modes for an asset'''

    def __init__(self, session):
        super(LoaderImporterPlugin, self).__init__(session)

    def _parse_run_event(self, event):
        '''
        Parse the event given on the :meth:`_run`. Returns method name to be
        executed and plugin_setting to be passed to the method.
        This is an override that modifies the plugin_setting['data'] to pass
        only the results of the collector stage of the current step.
        '''
        method, plugin_settings = super(
            LoaderImporterPlugin, self
        )._parse_run_event(event)
        data = plugin_settings.get('data')
        #We only want the data of the collector in this stage
        collector_result = []
        component_step = data[-1]
        if component_step.get('category') == 'plugin':
            return method, plugin_settings
        for component_stage in component_step.get("result"):
            if (
                    component_stage.get("name") == constants.COLLECTOR
            ):
                collector_result = component_stage.get("result")
                break
        if collector_result:
            plugin_settings['data'] = collector_result
        return method, plugin_settings

    def get_current_objects(self):
        #TODO: implement this function un the dcc plugin importer.py
        raise NotImplementedError

    def _run(self, event):
        self.old_objects = self.get_current_objects()
        self.logger.debug('Current objects : {}'.format(len(self.old_objects)))
        # Having this in a separate method, we can override the parse depending
        #  on the plugin type.
        self._method, self._plugin_settings = self._parse_run_event(event)

        context_data = self.plugin_settings.get('context_data')
        self.logger.debug('Current context : {}'.format(context_data))

        data = self.plugin_settings.get('data')
        self.logger.debug('Current data : {}'.format(data))

        options = self.plugin_settings.get('options')
        self.logger.debug('Current options : {}'.format(options))

        json_data = json.dumps(event['data'])
        if six.PY2:
            options[asset_const.ASSET_INFO_OPTIONS] = base64.b64encode(
                json_data
            )
        else:
            input_bytes = json_data.encode('utf8')
            options[asset_const.ASSET_INFO_OPTIONS] = base64.b64encode(
                input_bytes
            ).decode('ascii')

        asset_load_mode = options.get(asset_const.LOAD_MODE)

        ftrack_asset_class = self.get_asset_class(context_data, data, options)
        ftrack_node = ftrack_asset_class.init_ftrack_object()

        #TODO: if True, the assets willl be load as node
        # only, so the plugin will not be executed but if false the node will be
        # created and the asset will automatically be loaded executing the plugin.
        if not asset_const.LOAD_AS_NODE_ONLY:
            super_result = super(LoaderImporterPlugin, self)._run(event)
            self.new_data = self.get_current_objects()
            self.logger.debug(
                'Scene objects after load : {}'.format(len(self.new_data))
            )

        else:
            #TODO: we can return this or somehow execute the ftracknodes plugin or the ftrack asset class init object.
            super_result = {
                'plugin_name': self.plugin_name,
                'plugin_type': self.plugin_type,
                'method': self.method,
                'status': constants.SUCCESS_STATUS,
                'result': None,
                'execution_time': 0,
                'message': None,
                'user_data': user_data,
                'plugin_id': self.plugin_id
            }

        ftrack_asset_class.connect_objects(diff)

        #TODO: even if the asset_load_mode is open, if we should be creating the ftracknode if not exists, and maybe delete it on publish
        # if asset_load_mode == load_const.OPEN_MODE: #We will have to fix the constants here depending on what dcc we are
        #     self.logger.warning('{} not created, load mode is {} and not {}'.format(
        #         self.ftrack_asset_class, asset_load_mode, load_const.OPEN_MODE))
        #     return super_result

        #TODO: the _run_plugin method of the engine.init is expecting a return
        # result here. So if we don't execute the plugin we should be returning
        # something anyway.
        return super_result
