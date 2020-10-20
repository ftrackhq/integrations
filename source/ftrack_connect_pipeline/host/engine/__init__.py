# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

import logging
import ftrack_api
import copy


def getEngine(baseClass, engineType):
    '''Return the engine Class *subclass* of the given *baseClass* based on the
    *engineType*'''
    for subclass in baseClass.__subclasses__():
        if engineType == subclass.__name__:
            return subclass
        match = getEngine(subclass, engineType)
        if match:
            return match


class BaseEngine(object):

    engine_type='base'

    @property
    def hostid(self):
        '''Return the current hostid.'''
        return self._hostid

    @property
    def host(self):
        '''Return the current host type.'''
        return self._host

    def __init__(self, event_manager, host, hostid, asset_type):
        '''Initialise BaseEngine with *event_manager*, *host*, *hostid* and
        *asset_type*'''
        super(BaseEngine, self).__init__()

        self.asset_type = asset_type
        self.session = event_manager.session
        self._host = host
        self._hostid = hostid

        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )

        self.event_manager = event_manager

    def run_event(
            self, plugin_name, plugin_type, host_definition, data, options,
            context
    ):
        return ftrack_api.event.base.Event(
                    topic=constants.PIPELINE_RUN_PLUGIN_TOPIC,
                    data={
                        'pipeline': {
                            'plugin_name': plugin_name,
                            'plugin_type': plugin_type,
                            'type': 'plugin',
                            'host': host_definition
                        },
                        'settings':
                            {
                                'data': data,
                                'options': options,
                                'context': context
                            }
                    }
                )

    def pre_run_event(
            self, plugin_name, plugin_type, host_definition, data, options,
            context
    ):
        return ftrack_api.event.base.Event(
            topic=constants.PIPELINE_PRE_RUN_PLUGIN_TOPIC,
            data={
                'pipeline': {
                    'plugin_name': plugin_name,
                    'plugin_type': plugin_type,
                    'type': 'plugin',
                    'host': host_definition
                },
                'settings':
                    {
                        'data': data,
                        'options': options,
                        'context': context
                    }
            }
        )

    def _run_plugin(
            self, plugin, plugin_type, options=None, data=None, context=None,
            pre_run=False
    ):
        '''Run *plugin*, *plugin_type*, with given *options*, *data* and
        *context* and notify client with the status before and after execute
        the plugin'''
        plugin_name = plugin['plugin']
        start_data = {
            'plugin_name': plugin_name,
            'plugin_type': plugin_type,
            'status': constants.RUNNING_STATUS,
            'result': None,
            'execution_time': 0,
            'message': None
        }

        self._notify_client(plugin, start_data)

        result_data = copy.deepcopy(start_data)
        result_data['status'] = constants.UNKNOWN_STATUS

        for host_definition in reversed(self._host):
            if pre_run:
                event = self.pre_run_event(
                    plugin_name, plugin_type, host_definition, data, options,
                    context
                )
            else:
                event = self.run_event(
                    plugin_name, plugin_type, host_definition, data, options,
                    context
                )

            plugin_result_data = self.session.event_hub.publish(
                event,
                synchronous=True
            )
            if plugin_result_data:
                result_data= plugin_result_data[0]
                result_data['pre_run'] = pre_run
                break

        self._notify_client(plugin, result_data)
        self.logger.debug("_notify_client: {}".format(plugin, result_data))
        return result_data['status'], result_data['result']

    def _notify_client(self, plugin, result_data):
        '''Publish an event to notify client with *data*, plugin_name from
        *plugin*, *status* and *message*'''

        print "publishing notify client from engine"
        result_data['hostid'] = self.hostid
        if plugin:
            result_data['widget_ref'] = plugin.get('widget_ref')
        else:
            result_data['widget_ref'] = None

        event = ftrack_api.event.base.Event(
            topic=constants.PIPELINE_CLIENT_NOTIFICATION,
            data={
                'pipeline': result_data
            }
        )

        self.event_manager.publish(
            event,
        )

    def run(self, data):
        '''
        Override function run methods and plugins from the provided *data*
        Return result
        '''

        method = data.get('method', '')
        plugin = data.get('plugin', None)
        assets = data.get('assets', None)
        options = data.get('options', {})
        pre_run = data.get('pre_run', False)
        plugin_type = data.get('plugin_type', None)

        result = None

        if hasattr(self, method):
            callback_fn = getattr(self, method)
            status, result = callback_fn(assets, options, plugin)
            if isinstance(status, dict):
                if not all(status.values()):
                    raise Exception(
                        'An error occurred during the execution of '
                        'the method: {}'.format(method)
                    )
            else:
                bool_status = constants.status_bool_mapping[status]
                if not bool_status:
                    raise Exception(
                        'An error occurred during the execution of '
                        'the method: {}'.format(method)
                    )

        elif plugin:
            status, result = self._run_plugin(
                plugin, plugin_type,
                data=plugin.get('plugin_data'),
                options=plugin['options'],
                context=None,
                pre_run=pre_run
            )

            bool_status = constants.status_bool_mapping[status]
            if not bool_status:
                raise Exception(
                    'An error occurred during the execution of the plugin {}'
                    '\n status: {} \n result: {}'.format(
                        plugin['plugin'], status, result)
                )

        return result


from ftrack_connect_pipeline.host.engine.publish import *
from ftrack_connect_pipeline.host.engine.load import *
from ftrack_connect_pipeline.host.engine.asset_manager import *