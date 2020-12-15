# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

import logging
import ftrack_api
import copy


def getEngine(baseClass, engineType):
    '''
    Returns the Class or Subclass of the given *baseClass* that matches the
    name of the given *engineType*
    '''
    for subclass in baseClass.__subclasses__():
        if engineType == subclass.__name__:
            return subclass
        match = getEngine(subclass, engineType)
        if match:
            return match


class BaseEngine(object):
    '''
    Base engine class.
    '''

    engine_type='base'
    '''Engine type for this engine class'''

    @property
    def host_id(self):
        '''Returns the current host id.'''
        return self._host_id

    @property
    def host_types(self):
        '''Return the current host type.'''
        return self._host_types

    def __init__(self, event_manager, host_types, host_id, asset_type):
        '''
        Initialise HostConnection with instance of
        :class:`~ftrack_connect_pipeline.event.EventManager` , and *host*,
        *hostid* and *asset_type*

        *host* : Host type.. (ex: python, maya, nuke....)
        *hostid* : Host id.
        *asset_type* : If engine is initialized to publish or load, the asset
        type should be specified.
        '''
        super(BaseEngine, self).__init__()

        self.asset_type = asset_type
        self.session = event_manager.session
        self._host_types = host_types
        self._host_id = host_id

        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )

        self.event_manager = event_manager

    def run_event(
            self, plugin_name, plugin_type, host_type, data, options,
            context, method
    ):
        '''
        Returns an :class:`ftrack_api.event.base.Event` with the topic
        :const:`~ftrack_connnect_pipeline.constants.PIPELINE_RUN_PLUGIN_TOPIC`
        with the data of the given *plugin_name*, *plugin_type*,
        *host_definition*, *data*, *options*, *context*, *method*

        *plugin_name* : Name of the plugin.

        *plugin_type* : Type of plugin.

        *host_definition* : Host type.

        *data* : data to pass to the plugin.

        *options* : options to pass to the plugin

        *context* : result of the context plugin containing the context_id,
        aset_name... Or None

        *method* : Method of the plugin to be executed.

        '''
        return ftrack_api.event.base.Event(
                    topic=constants.PIPELINE_RUN_PLUGIN_TOPIC,
                    data={
                        'pipeline': {
                            'plugin_name': plugin_name,
                            'plugin_type': plugin_type,
                            'method': method,
                            'type': 'plugin',
                            'host_type': host_type
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
            method='run'
    ):
        '''
        Returns the result of running the plugin with the event returned from
        :meth:`run_event` using the given *plugin*, *plugin_type*,
        *options*, *data*, *context*, *method*

        *plugin* : Plugin definition, a dictionary with the plugin information.

        *plugin_type* : Type of plugin.


        *options* : options to pass to the plugin

        *data* : data to pass to the plugin.

        *context* : result of the context plugin containing the context_id,
        aset_name... Or None

        *method* : Method of the plugin to be executed.

        '''

        plugin_name = plugin['plugin']
        start_data = {
            'plugin_name': plugin_name,
            'plugin_type': plugin_type,
            'method': method,
            'status': constants.RUNNING_STATUS,
            'result': None,
            'execution_time': 0,
            'message': None
        }

        self._notify_client(plugin, start_data)

        result_data = copy.deepcopy(start_data)
        result_data['status'] = constants.UNKNOWN_STATUS

        for host_type in reversed(self._host_types):
            event = self.run_event(
                plugin_name, plugin_type, host_type, data, options,
                context, method
            )

            plugin_result_data = self.session.event_hub.publish(
                event,
                synchronous=True
            )
            if plugin_result_data:
                result_data = plugin_result_data[0]
                break

        self._notify_client(plugin, result_data)
        self.logger.debug("_notify_client: {}".format(plugin, result_data))
        return result_data['status'], result_data['result']

    def _notify_client(self, plugin, result_data):
        '''
        Publish an :class:`ftrack_api.event.base.Event` with the topic
        :const:`~ftrack_connnect_pipeline.constants.PIPELINE_CLIENT_NOTIFICATION`
        to notify the client of the given *plugin* result *result_data*.

        *plugin* : Plugin definition, a dictionary with the plugin information.

        *result_data* : Result of the plugin execution.

        '''

        result_data['host_id'] = self.host_id
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

    def run_definition(self, data):
        '''
        Returns a :exc:`NotImplementedError`.
        '''

        raise(NotImplementedError)

    def run(self, data):
        '''
        Executes the :meth:`_run_plugin` with the provided *data*.
        Returns the result of the mentioned method.

        *data* : pipeline['data'] provided from the client host connection at
        :meth:`~ftrack_connect_pipeline.client.HostConnection.run`
        '''

        method = data.get('method', 'run')
        plugin = data.get('plugin', None)
        plugin_type = data.get('plugin_type', None)

        result = None

        if plugin:
            status, result = self._run_plugin(
                plugin, plugin_type,
                data=plugin.get('plugin_data'),
                options=plugin['options'],
                context=None,
                method=method
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