# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import logging
import ftrack_api
from ftrack_connect_pipeline import constants

def getEngine(baseClass, runnerType):
    for subclass in baseClass.__subclasses__():
        if runnerType == subclass.__name__:
            return subclass

class BaseRunner(object):

    @property
    def hostid(self):
        '''Return the current hostid.'''
        return self._hostid

    @property
    def host(self):
        '''Return the current host type.'''
        return self._host

    def __init__(self, event_manager, host,  hostid, asset_type):
        '''Initialise publish runnder with *session*, *package_definitions*, *host*, *ui* and *hostid*.'''
        super(BaseRunner, self).__init__()
        self.component_stages_order = [
            constants.COLLECTOR,
            constants.VALIDATOR,
            constants.OUTPUT
        ]

        self.asset_type = asset_type
        self.session = event_manager.session
        self._host = host
        self._hostid = hostid

        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )

        self.event_manager = event_manager

    def _run_plugin(self, plugin, plugin_type, options=None, data=None, context=None):
        '''Run *plugin*, *plugin_type*, with given *options*, *data* and *context*'''
        plugin_name = plugin['plugin']

        event = ftrack_api.event.base.Event(
            topic=constants.PIPELINE_RUN_PLUGIN_TOPIC,
            data={
                'pipeline': {
                    'plugin_name': plugin_name,
                    'plugin_type': plugin_type,
                    'type': 'plugin',
                    'host': self.host
                },
                'settings':
                    {
                        'data': data,
                        'options': options,
                        'context': context
                    }
            }
        )

        data = self.session.event_hub.publish(
            event,
            synchronous=True
        )
        result = data[0]['result']
        status = data[0]['status']

        return status, result

    def run_context(self, context_plugins):
        '''Run *context_pligins*.'''
        statuses = []
        results = {}
        for plugin in context_plugins:
            status, result = self._run_plugin(
                plugin, constants.CONTEXTS,
                context=plugin['options']
            )
            bool_status = constants.status_bool_mapping[status]
            statuses.append(bool_status)
            # rise error here if result is none
            results.update(result)

        return statuses, results

    def run_component(self, component_name, component_stages, context_data):
        '''Run component plugins for *component_name*, *component_stages* with *context_data*.'''
        results = {}
        statuses = {}

        for component_stage in component_stages:
            for stage_name in self.component_stages_order:
                if stage_name != component_stage['name']:
                    continue

                plugins = component_stage['plugins']

                if not plugins:
                    continue

                collected_data = results.get(constants.COLLECTOR, [])
                stages_result = []
                stage_status = []

                for plugin in plugins:

                    plugin_options = plugin['options']
                    plugin_options['component_name'] = component_name

                    status, result = self._run_plugin(
                        plugin, stage_name,
                        data=collected_data,
                        options=plugin_options,
                        context=context_data
                    )

                    # Merge list of lists.
                    if result and isinstance(result, list):
                        result = result[0]

                    bool_status = constants.status_bool_mapping[status]
                    stage_status.append(bool_status)
                    stages_result.append(result)

                results[stage_name] = stages_result
                statuses[stage_name] = all(stage_status)

        return statuses, results

    def run_finaliser(self, finaliser_plugins, finaliser_data, context_data):
        '''Run component plugins for *component_name*, *component_stages* with *context_data*.'''
        statuses = []
        results = []

        for plugin in finaliser_plugins:
            status, result = self._run_plugin(
                plugin, constants.FINALISERS,
                data=finaliser_data,
                options=plugin['options'],
                context=context_data
            )
            bool_status = constants.status_bool_mapping[status]
            statuses.append(bool_status)
            results.append(result)

        return statuses, results

    def run(self, data):
        '''Run the package definition based on the result of incoming *event*.'''
        context_plugins = data[constants.CONTEXTS]
        context_status, context_result = self.run_context(context_plugins)
        if not all(context_status):
            return
        context_result['asset_type'] = self.asset_type

        components = data[constants.COMPONENTS]
        components_result = []
        components_status = []

        for component in components:
            component_name = component["name"]
            component_stages = component["stages"]
            component_status, component_result = self.run_component(
                component_name, component_stages, context_result
            )

            if not all(component_status.values()):
                continue

            components_status.append(component_status)
            components_result.append(component_result)

        print components_status, components_result

        finaliser_plugins = data[constants.FINALISERS]

        finaliser_data = {}
        for item in components_result:
            for output in item.get(constants.OUTPUT):
                if not output:
                    continue

                for key, value in output.items():
                    finaliser_data[key] = value

        finalisers_status, finalisers_result = self.run_finaliser(
            finaliser_plugins, finaliser_data, context_result
        )
        if not all(finalisers_status):
            return

        return True

from ftrack_connect_pipeline.host.runner.publish import *
from ftrack_connect_pipeline.host.runner.load import *