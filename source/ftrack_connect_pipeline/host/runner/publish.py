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
            constants.COLLECT,
            constants.VALIDATE,
            constants.OUTPUT
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

        self._notify_client(result, plugin, status)

        return result

    def _notify_client(self, data, plugin, status):
        '''Notify client with *data* for *plugin*'''

        widget_ref = plugin['widget_ref']

        pipeline_data = {
            'hostid': self.hostid,
            'widget_ref': widget_ref,
            'data': data,
            'status': status
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
        results = {}
        for plugin in context_pligins:
            result = self._run_plugin(
                plugin, constants.CONTEXT,
                context=plugin['options']
            )
            self.logger.debug('context result : {}'.format(result))
            results.update(result)

        return results

    def run_component(self, component_name, component_stages, context_data):
        '''Run component plugins for *component_name*, *component_stages* with *context_data*.'''
        results = {}

        for stage_name in self.component_stages_order:
            plugins = component_stages.get(stage_name)
            if not plugins:
                continue

            collected_data = results.get(constants.COLLECT, [])
            stages_result = []

            for plugin in plugins:

                plugin_options = plugin['options']
                plugin_options['component_name'] = component_name

                result = self._run_plugin(
                    plugin, stage_name,
                    data=collected_data,
                    options=plugin_options,
                    context=context_data
                )

                # Merge list of lists.
                if result and isinstance(result, list):
                    result = result[0]

                stages_result.append(result)

            results[stage_name] = stages_result

        return results

    def run_publish(self, publish_plugins, publish_data, context_data):
        '''Run component plugins for *component_name*, *component_stages* with *context_data*.'''
        results = []
        for plugin in publish_plugins:
            result = self._run_plugin(
                plugin, constants.PUBLISH,
                data=publish_data,
                options=plugin['options'],
                context=context_data
            )

            results.append(result)

        return results

    def run(self, event):
        '''Run the package definition based on the result of incoming *event*.'''
        data = event['data']['pipeline']['data']
        publish_package = data['package']
        asset_type = self.packages[publish_package]['type']

        context_plugins = data[constants.CONTEXT]
        context_result = self.run_context(context_plugins)
        context_result['asset_type'] = asset_type

        components_plugins = data[constants.COMPONENTS]
        components_result = []
        for component_name, component_stages in components_plugins.items():
            component_result = self.run_component(
                component_name, component_stages, context_result
            )
            components_result.append(component_result)

        publish_plugins = data[constants.PUBLISH]

        publish_data = {}
        for item in components_result:
            for output in item.get(constants.OUTPUT):
                if not output:
                    continue

                for key, value in output.items():
                    publish_data[key] = value

        publish_result = self.run_publish(
            publish_plugins, publish_data, context_result
        )

        self.logger.info(publish_result)






