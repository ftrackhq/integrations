# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import logging
import ftrack_api

from jsonschema import validate as _validate_jsonschema
from ftrack_connect_pipeline import constants

logger = logging.getLogger(__name__)


def get_schema(definition_type, schemas):
    for schema in schemas:
        if definition_type == schema['title'].lower():
            return schema
    return None


def validate_schema(schemas, definition):
    schema = get_schema(definition['type'], schemas)
    _validate_jsonschema(definition, schema)


class PluginDiscoverValidation(object):
    '''Plugin Discover base class'''

    def __init__(self, session, host):
        '''Initialise PluginDiscoverValidation with *session*, *host*.

        *session* should be the :class:`ftrack_api.session.Session` instance
        to use for communication with the server.

        *host* is a list of valid host definitions.

        '''
        super(PluginDiscoverValidation, self).__init__()

        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )

        self.session = session
        self.host = host

    def validate_publishers_plugins(self, publishers):
        idxs_to_pop = []
        for definition in publishers:
            valid_definition = True
            # context plugins
            if not self.vaildate_contexts_plugins(
                    definition[constants.CONTEXTS], definition["name"]):
                valid_definition = False
            if not self.validate_components_plugins(
                    definition[constants.COMPONENTS], definition["name"]):
                valid_definition = False
            if not self.vaildate_finalisers_plugins(
                    definition[constants.FINALISERS], definition["name"]):
                valid_definition = False
            if not valid_definition:
                idx = publishers.index(definition)
                idxs_to_pop.append(idx)
                self.logger.warning(
                    'The definition {} from type {} contains invalid plugins '
                    'and will not be used'.format(
                        definition["name"], 'publishers'
                    )
                )

        return idxs_to_pop or None

    def validate_loaders_plugins(self, loaders):
        idxs_to_pop = []
        for definition in loaders:
            valid_definition = True
            # context plugins
            if not self.validate_components_plugins(
                    definition[constants.COMPONENTS], definition["name"]):
                valid_definition = False
            if not valid_definition:
                idx = loaders.index(definition)
                idxs_to_pop.append(idx)
                self.logger.warning(
                    'The definition {} from type {} contains invalid plugins '
                    'and will not be used'.format(
                        definition["name"], 'publishers'
                    )
                )

        return idxs_to_pop or None

    def vaildate_contexts_plugins(self, context_stage, definition_name):
        is_valid = True
        stage_name = context_stage['name']
        for context_plugin in context_stage['plugins']:
            if not self._discover_plugin(context_plugin,
                                         stage_name):
                is_valid = False
                self.logger.warning(
                    'Could not discover plugin {} for stage {} in {}'.format(
                        context_plugin['plugin'], stage_name, definition_name)
                )
        return is_valid

    def validate_components_plugins(self, components_list, definition_name):
        # components plugins
        is_valid = True
        for component in components_list:
            for component_stage in component['stages']:
                stage_name = component_stage['name']
                for component_plugin in component_stage['plugins']:
                    if not self._discover_plugin(component_plugin, stage_name):
                        is_valid = False
                        self.logger.warning(
                            'Could not discover plugin {} for '
                            'stage {} in {}'.format(
                                component_plugin['plugin'], stage_name,
                                definition_name)
                        )
        return is_valid

    def vaildate_finalisers_plugins(self, finaliser_stage, definition_name):
        is_valid = True
        stage_name = finaliser_stage['name']
        for publisher_plugin in finaliser_stage['plugins']:
            if not self._discover_plugin(publisher_plugin,
                                         stage_name):
                is_valid = False
                self.logger.warning(
                    'Could not discover plugin {} for {} in {}'.format(
                        publisher_plugin['plugin'], stage_name, definition_name)
                )
        return is_valid

    def _discover_plugin(self, plugin, plugin_type):
        '''Checks if the *plugin* of type *plugin_type* for the current host
        '''
        plugin_name = plugin['plugin']

        for host_definition in reversed(self.host):
            data = {
                'pipeline': {
                    'plugin_name': plugin_name,
                    'plugin_type': plugin_type,
                    'type': 'plugin',
                    'host': host_definition
                }
            }
            event = ftrack_api.event.base.Event(
                topic=constants.PIPELINE_DISCOVER_PLUGIN_TOPIC,
                data=data
            )

            plugin_result = self.session.event_hub.publish(
                event,
                synchronous=True
            )

            if plugin_result:
                plugin_result = plugin_result[0]
                self.logger.info(
                    'plugin {} found for definition host {}'.format(
                        plugin_name, host_definition
                    )
                )
                break
            self.logger.info(
                'plugin {} not found for definition host {}'.format(
                    plugin_name, host_definition
                )
            )

        return plugin_result
