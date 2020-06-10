# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import copy
import logging
import ftrack_api
from ftrack_connect_pipeline import constants


def getEngine(baseClass, engineType):
    '''Return the engine Class *subclass* of the given *baseClass* based on the
    *engineType*'''
    for subclass in baseClass.__subclasses__():
        if engineType == subclass.__name__:
            return subclass


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

    def _run_plugin(self, plugin, plugin_type, options=None, data=None,
                    context=None):
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

    def run_context(self, context_stage):
        '''Run *context_pligins*.
        Raise Exception if any plugin returns a False status
        Returns *statuses* (List) *results* (List)'''
        statuses = []
        results = {}

        stage_name = context_stage['name']
        plugin_type = '{}.{}'.format(self.engine_type, stage_name)
        for plugin in context_stage['plugins']:
            status, result = self._run_plugin(
                plugin, plugin_type,
                options=plugin['options']
            )
            bool_status = constants.status_bool_mapping[status]
            if not bool_status:
                raise Exception(
                    'An error occurred during the execution of the context '
                    'plugin {}\n stage: {} \n status: {} \n result: {}'.format(
                        plugin['plugin'], stage_name, status, result)
                )

            statuses.append(bool_status)
            results.update(result)

        return statuses, results

    def run_component(self, component_name, component_stages, context_data,
                      stages_order):
        '''Run component plugins for *component_name*, *component_stages* with
        *context_data* with the
        provided *stages_order*.
        Raise Exception if any plugin returns a False status
        Returns *statuses* (List) *results* (List)'''
        results = {}
        statuses = {}

        for component_stage in component_stages:
            for stage_name in stages_order:
                if stage_name != component_stage['name']:
                    continue

                plugins = component_stage['plugins']

                if not plugins:
                    continue

                plugin_type = '{}.{}'.format(self.engine_type, stage_name)

                collected_data = results.get(constants.COLLECTOR, [])
                stages_result = []
                stage_status = []

                for plugin in plugins:

                    plugin_options = plugin['options']
                    plugin_options['component_name'] = component_name
                    status, result = self._run_plugin(
                        plugin, plugin_type,
                        data=collected_data,
                        options=plugin_options,
                        context=context_data
                    )

                    bool_status = constants.status_bool_mapping[status]
                    stage_status.append(bool_status)
                    if result and isinstance(result, list):
                        stages_result.extend(result)
                    else:
                        stages_result.append(result)
                    if not bool_status:
                        self.logger.error(
                            'An error occurred during the execution of the '
                            'component plugin {} \n status: {} \n '
                            'result: {}'.format(
                                plugin['plugin'], status, result
                            )
                        )

                results[stage_name] = stages_result
                statuses[stage_name] = all(stage_status)
                if not statuses[stage_name]:
                    raise Exception(
                        'An error occurred during the execution of '
                        'the stage {} \n status: {} \n result: {}'.format(
                            stage_name, statuses[stage_name], results[stage_name]
                        )
                    )

        return statuses, results

    def run_finaliser(self, finaliser_stage, finaliser_data, context_data):
        '''Run finaliser plugins for *finaliser_plugins* with *finaliser_data*
        and *context_data*.
        Raise Exception if any plugin returns a False status
        Returns *statuses* (List) *results* (List)'''
        statuses = []
        results = []

        stage_name = finaliser_stage['name']
        plugin_type = '{}.{}'.format(self.engine_type, stage_name)
        for plugin in finaliser_stage['plugins']:
            status, result = self._run_plugin(
                plugin, plugin_type,
                data=finaliser_data,
                options=plugin['options'],
                context=context_data
            )
            bool_status = constants.status_bool_mapping[status]
            if not bool_status:
                raise Exception(
                    'An error occurred during the execution of the finaliser '
                    'plugin {}\n stage: {} \n status: {} \n result: {}'.format(
                        plugin['plugin'], stage_name, status, result)
                )
            statuses.append(bool_status)
            results.append(result)

        return statuses, results

    def run(self, data):
        '''Run packages from the provided data
        *data* the json schema
        Raise Exception if any context plugin, component plugin or finaliser
        plugin returns a False status
        Returns Bool'''

        context_plugins = data[constants.CONTEXTS]
        context_status, context_result = self.run_context(context_plugins)
        if not all(context_status):
            raise Exception('An error occurred during the execution of the '
                            'context')
        context_result['asset_type'] = self.asset_type

        components = data[constants.COMPONENTS]
        components_result = []
        components_status = []

        for component in components:
            component_name = component['name']
            component_stages = component['stages']
            component_status, component_result = self.run_component(
                component_name, component_stages, context_result,
                data['_config']['stage_order']
            )

            if not all(component_status.values()):
                raise Exception('An error occurred during the execution of the '
                                'component name {}'.format(component_name))

            components_status.append(component_status)
            components_result.append(component_result)

        finaliser_plugins = data[constants.FINALISERS]
        finaliser_data = {}
        for item in components_result:
            last_component = constants.OUTPUT
            if constants.POST_IMPORT in list(item.keys()):
                last_component = constants.POST_IMPORT
            for output in item.get(last_component):
                if not output:
                    continue

                for key, value in list(output.items()):
                    finaliser_data[key] = value

        finalisers_status, finalisers_result = self.run_finaliser(
            finaliser_plugins, finaliser_data, context_result
        )
        if not all(finalisers_status):
            raise Exception('An error occurred during the execution of the '
                            'finalisers')

        return True

from ftrack_connect_pipeline.host.engine.publish import *
from ftrack_connect_pipeline.host.engine.load import *