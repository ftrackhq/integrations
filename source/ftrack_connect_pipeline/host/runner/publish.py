# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import logging
import ftrack_api
from ftrack_connect_pipeline import constants
from ftrack_connect_pipeline.event import EventManager
from ftrack_connect_pipeline import exception
from ftrack_connect_pipeline import utils


class PublisherRunner(object):

    @property
    def hostid(self):
        '''Return the current hostid.'''
        return self._hostid

    @property
    def host(self):
        '''Return the current host type.'''
        return self._host

    @property
    def ui(self):
        '''Return the current ui type.'''
        return self._ui

    def __init__(self, session, package_definitions, host,  ui, hostid):
        '''Initialise publish runnder with *session*, *package_definitions*, *host*, *ui* and *hostid*.'''
        self.__remote_events = utils.remote_event_mode()

        self.component_stages_order = [
            constants.COLLECTORS,
            constants.VALIDATORS,
            constants.OUTPUTS
        ]

        self.session = session
        self._host = host
        self._ui = ui
        self._hostid = hostid
        self.packages = package_definitions

        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )

        self.event_manager = EventManager(session)

        session.event_hub.subscribe(
            'topic={} and data.pipeline.hostid={}'.format(
                constants.PIPELINE_RUN_HOST_PUBLISHER, self.hostid
            ),
            self.run
        )

    def _run_plugin(self, plugin, plugin_type, options=None, data=None, context=None):
        '''Run *plugin*, *plugin_type*, with given *options*, *data* and *context*'''
        plugin_name = plugin['plugin']

        self._notify_client(None, plugin, constants.RUNNING_STATUS)

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
        message = data[0]['message']

        self._notify_client(result, plugin, status, message)

        return status, result

    def _notify_client(self, data, plugin, status, message=None):
        '''Notify client with *data* for *plugin*'''

        widget_ref = plugin['widget_ref']

        pipeline_data = {
            'hostid': self.hostid,
            'widget_ref': widget_ref,
            'data': data,
            'status': status,
            'message': message
        }

        event = ftrack_api.event.base.Event(
            topic=constants.PIPELINE_UPDATE_UI,
            data={
                'pipeline':pipeline_data
            }
        )

        self.event_manager.publish(
            event,
            remote=self.__remote_events
        )

    def run_context(self, context_pligins):
        '''Run *context_pligins*.'''
        statuses = []
        results = {}
        for plugin in context_pligins:
            status, result = self._run_plugin(
                plugin, constants.CONTEXT,
                context=plugin['options']
            )

            bool_status = constants.status_bool_mapping[status]
            statuses.append(bool_status)

            results.update(result)

        return statuses, results

    def run_component(self, component_name, component_stages, context_data):
        '''Run component plugins for *component_name*, *component_stages* with *context_data*.'''
        results = {}
        statuses = {}

        for component_stage in component_stages:
            for stage_name in self.component_stages_order:
                plugins = component_stage.get(stage_name)
                if not plugins:
                    continue

                collected_data = results.get(constants.COLLECTORS, [])
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

    def run_publish(self, publish_plugins, publish_data, context_data):
        '''Run component plugins for *component_name*, *component_stages* with *context_data*.'''
        statuses = []
        results = []

        self.logger.debug("publish_plugins --->  {} publish_data --->  {} context_data ---> {}".format(publish_plugins, publish_data, context_data))

        for plugin in publish_plugins:
            status, result = self._run_plugin(
                plugin, constants.PUBLISHERS,
                data=publish_data,
                options=plugin['options'],
                context=context_data
            )
            bool_status = constants.status_bool_mapping[status]
            statuses.append(bool_status)
            results.append(result)

        return statuses, results

    def run(self, event):
        '''Run the package definition based on the result of incoming *event*.'''
        data = event['data']['pipeline']['data']

        publish_package = data['package']
        asset_type = self.packages[publish_package]['type']

        context_plugins = data[constants.CONTEXT]
        context_status, context_result = self.run_context(context_plugins)

        if not all(context_status):
            return

        context_result['asset_type'] = asset_type

        publisher_components = data[constants.COMPONENTS]
        components_result = []
        components_status = []

        for publisher_component in publisher_components:
            component_name = publisher_component["name"]
            component_stages = publisher_component["stages"]
            component_status, component_result = self.run_component(
                component_name, component_stages, context_result
            )
            if not all(component_status.values()):
                continue

            components_status.append(component_status)
            components_result.append(component_result)

        publish_plugins = data[constants.PUBLISHERS]

        publish_data = {}
        for item in components_result:
            for output in item.get(constants.OUTPUTS):
                if not output:
                    continue

                for key, value in output.items():
                    publish_data[key] = value

        self.logger.debug("publish data --> {} ".format(publish_data))
        publish_status, publish_result = self.run_publish(
            publish_plugins, publish_data, context_result
        )
        if not all(context_status):
            return






