# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

import json
import six
import base64

from ftrack_connect_pipeline import constants
from ftrack_connect_pipeline.plugin import base
from ftrack_connect_pipeline.asset.asset_info import FtrackAssetInfo
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
    '''Required return exporters'''

    open_modes = {}
    '''Available open modes for an asset'''

    dependency_open_mode = ''
    '''Default defendency open Mode'''

    json_data = {}
    '''Extra json data with the current open options'''

    def __init__(self, session):
        super(OpenerImporterPlugin, self).__init__(session)

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

        # Get Asset version entity to generate asset info
        asset_version_entity = self.session.query(
            'select version from AssetVersion where id is "{}"'.format(
                context_data[asset_const.VERSION_ID]
            )
        ).one()

        # Get Component name from collector data.
        component_name = None
        component_path = None
        component_id = None
        for collector in data:
            if not isinstance(collector['result'], dict):
                continue
            else:
                component_name = collector['result'].get(
                    asset_const.COMPONENT_NAME
                )
                component_path = collector['result'].get(
                    asset_const.COMPONENT_PATH
                )
                component_id = collector['result'].get(
                    asset_const.COMPONENT_ID
                )
                break

        asset_info = FtrackAssetInfo.create(
            asset_version_entity,
            component_name=component_name,
            component_path=component_path,
            component_id=component_id,
            load_mode=options.get(asset_const.LOAD_MODE),
            asset_info_options=options.get(asset_const.ASSET_INFO_OPTIONS),
        )

        self.asset_info = asset_info
        self.ftrack_object_manager.create_new_dcc_object()

        result = {'asset_info': self.asset_info, 'dcc_object': self.dcc_object}
        return result

    def open_asset(self, context_data=None, data=None, options=None):
        '''Alternative plugin method to only open the asset in the scene'''

        asset_info = options.get('asset_info')
        self.asset_info = asset_info
        dcc_object = self.DccObject(
            from_id=asset_info[asset_const.ASSET_INFO_ID]
        )
        self.dcc_object = dcc_object
        # Remove asset_info from the options as it is not needed anymore
        options.pop('asset_info')
        # Execute the run method to load the objects
        run_result = self.run(context_data, data, options)
        #  Query all the objects from the scene
        self.new_data = self.get_current_objects()
        self.logger.debug(
            'Scene objects after load : {}'.format(len(self.new_data))
        )
        diff = self.new_data.difference(self.old_data)

        # Set asset_info as loaded.
        self.ftrack_object_manager.objects_loaded = True

        # Connect scene objects to ftrack node
        self.ftrack_object_manager.connect_objects(diff)

        result = {
            'asset_info': self.asset_info,
            'dcc_object': self.dcc_object,
            'result': run_result,
        }

        return result

    def init_and_open(self, context_data=None, data=None, options=None):
        '''Alternative plugin method to init and open the node and the assets
        into the scene'''

        init_nodes_result = self.init_nodes(
            context_data=context_data, data=data, options=options
        )
        options['asset_info'] = init_nodes_result.get('asset_info')
        load_asset_result = self.open_asset(
            context_data=context_data, data=data, options=options
        )
        return load_asset_result

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
