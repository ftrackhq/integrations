# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

import logging
import ftrack_api
from ftrack_connect_pipeline import constants
from ftrack_connect_pipeline.host.engine import BaseEngine


class BaseLoaderPublisherEngine(BaseEngine):
    engine_type = 'loader_publisher'

    def __init__(self, event_manager, host, hostid, asset_type):
        '''Initialise LoaderEngine with *event_manager*, *host*, *hostid* and
        *asset_type*'''
        super(BaseLoaderPublisherEngine, self).__init__(event_manager, host, hostid,
                                           asset_type)

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

    def run_finalizer(self, finalizer_stage, finalizer_data, context_data):
        '''Run finalizer plugins for *finalizer_plugins* with *finalizer_data*
        and *context_data*.
        Raise Exception if any plugin returns a False status
        Returns *statuses* (List) *results* (List)'''
        statuses = []
        results = []

        stage_name = finalizer_stage['name']
        plugin_type = '{}.{}'.format(self.engine_type, stage_name)
        for plugin in finalizer_stage['plugins']:
            status, result = self._run_plugin(
                plugin, plugin_type,
                data=finalizer_data,
                options=plugin['options'],
                context=context_data
            )
            bool_status = constants.status_bool_mapping[status]
            if not bool_status:
                raise Exception(
                    'An error occurred during the execution of the finalizer '
                    'plugin {}\n stage: {} \n status: {} \n result: {}'.format(
                        plugin['plugin'], stage_name, status, result)
                )
            statuses.append(bool_status)
            results.append(result)

        return statuses, results

    def run(self, data):
        '''Run packages from the provided data
        *data* the json schema
        Raise Exception if any context plugin, component plugin or finalizer
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
            component_enabled = component['enabled']
            if not component_enabled:
                self.logger.info('Skipping component {} as it been disabled'.format(component_name))
                continue

            component_status, component_result = self.run_component(
                component_name, component_stages, context_result,
                data['_config']['stage_order']
            )

            if not all(component_status.values()):
                raise Exception('An error occurred during the execution of the '
                                'component name {}'.format(component_name))

            components_status.append(component_status)
            components_result.append(component_result)

        finalizer_plugins = data[constants.FINALIZERS]
        finalizer_data = {}
        for item in components_result:
            last_component = constants.OUTPUT
            if constants.POST_IMPORT in item.keys():
                last_component = constants.POST_IMPORT
            for output in item.get(last_component):
                if not output:
                    continue

                for key, value in output.items():
                    finalizer_data[key] = value

        finalizers_status, finalizers_result = self.run_finalizer(
            finalizer_plugins, finalizer_data, context_result
        )
        if not all(finalizers_status):
            raise Exception('An error occurred during the execution of the '
                            'finalizers')

        return True


