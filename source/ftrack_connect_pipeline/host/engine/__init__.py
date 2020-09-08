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

    def _run_plugin(
            self, plugin, plugin_type, options=None, data=None, context=None
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
            event = ftrack_api.event.base.Event(
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
            plugin_result_data = self.session.event_hub.publish(
                event,
                synchronous=True
            )
            if plugin_result_data:
                result_data= plugin_result_data[0]
                break

        self._notify_client(plugin, result_data)
        self.logger.debug("_notify_client: {}".format(plugin, result_data))
        return result_data['status'], result_data['result']

    def _notify_client(self, plugin, result_data):
        '''Publish an event to notify client with *data*, plugin_name from
        *plugin*, *status* and *message*'''

        result_data['hostid'] = self.hostid
        result_data['widget_ref'] = plugin.get('widget_ref')

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
        raise NotImplementedError


from ftrack_connect_pipeline.host.engine.publish import *
from ftrack_connect_pipeline.host.engine.load import *
from ftrack_connect_pipeline.host.engine.asset_manager import *