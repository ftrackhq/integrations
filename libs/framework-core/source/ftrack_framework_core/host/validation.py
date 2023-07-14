# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

import logging
import ftrack_api

from jsonschema import validate as _validate_jsonschema
from ftrack_framework_core import constants

logger = logging.getLogger(__name__)

#TODO: this should be moved to definition folder
def get_schema(definition_type, schemas):
    '''
    Returns the schema in the given *schemas* for the given *definition_type*

    *definition_type* : Type of the definition. (asset_manager, publisher...)

    *schemas* : List of schemas.
    '''
    for schema in schemas:
        if definition_type == schema['title'].lower():
            return schema
    return None

#TODO: this should be moved to validate folder with the definitions
def validate_schema(schemas, definition):
    '''
    Validates the schema of the given *definition* from the given *schemas*
    using the _validate_jsonschema function of the jsonschema.validate library.

    *schemas* : List of schemas.

    *definition* : Definition to be validated against the schema.
    '''
    schema = get_schema(definition['type'], schemas)
    _validate_jsonschema(definition, schema)

#TODO: this should be moved to plugin folder or definition folder(analize it carefully as definition object has plugins as well.
# Also separate validation from discovery and move validation to the validation folder and discovery to the collect or discovery module in plugins.
class PluginDiscoverValidation(object):
    '''Plugin discover validation base class'''

    @property
    def session(self):
        '''
        Returns instance of :class:`ftrack_api.session.Session`
        '''
        return self._event_manager.session

    @property
    def event_manager(self):
        '''Returns instance of
        :class:`~ftrack_framework_core.event.EventManager`'''
        return self._event_manager

    @property
    def host_types(self):
        '''Return supported host types'''
        return self._host_types

    def __init__(self, event_manager, host_types):
        '''

        Initialise PluginDiscoverValidation with instance of
        :class:`ftrack_api.session.Session` and *host_types*.

        *host_types* : List of compatible host types. (maya, python, nuke....)

        '''
        super(PluginDiscoverValidation, self).__init__()

        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )
        self._event_manager = event_manager

        self._host_types = host_types

    # This method should go to the validation folder in the plugins module
    def validate_plugins(self, definitions, schema_type):
        '''
        Validates all the definitions in the given *definitions* definitions
        calling the :meth:`validate_context_plugins`,
        :meth:`validate_components_plugins`,
        :meth:`vaildate_finalizers_plugins`.

        Returns the invalid definition indices.

        *definitions* : List of definitions (opener, loader, publisher and so on).

        '''
        # TODO: Improve this code to try to have it all in one loop and manage it from constants.
        idxs_to_pop = []
        for definition in definitions:
            valid_definition = True
            # context plugins
            try:
                if not self.vaildate_definition_plugins(
                    definition[constants.CONTEXTS],
                    definition['name'],
                    schema_type,
                ):
                    valid_definition = False
                    self.logger.debug(
                        'Could not validate plugins of definition: {} step: {} '
                        'of schema type: {}'.format(
                            definition['name'], constants.CONTEXTS, schema_type
                        )
                    )
            except Exception as e:
                self.logger.error(
                    'Could not validate {} contexts steps: {}'.format(
                        schema_type, e
                    )
                )
                valid_definition = False
            # component plugins
            try:
                if not self.vaildate_definition_plugins(
                    definition[constants.COMPONENTS],
                    definition['name'],
                    schema_type,
                ):
                    valid_definition = False
                    self.logger.debug(
                        'Could not validate plugins of definition: {} step: {} '
                        'of schema type: {}'.format(
                            definition['name'],
                            constants.COMPONENTS,
                            schema_type,
                        )
                    )
            except Exception as e:
                self.logger.error(
                    'Could not validate {} components steps: {}'.format(
                        schema_type, e
                    )
                )
                valid_definition = False
            # finalizer plugins
            try:
                if not self.vaildate_definition_plugins(
                    definition[constants.FINALIZERS],
                    definition['name'],
                    schema_type,
                ):
                    valid_definition = False
                    self.logger.debug(
                        'Could not validate plugins of definition: {} step: {} '
                        'of schema type: {}'.format(
                            definition['name'],
                            constants.FINALIZERS,
                            schema_type,
                        )
                    )
            except Exception as e:
                self.logger.error(
                    'Could not validate {} finalizers steps: {}'.format(
                        schema_type, e
                    )
                )
                valid_definition = False
            if not valid_definition:
                idx = definitions.index(definition)
                idxs_to_pop.append(idx)
                self.logger.debug(
                    'The definition {} from type {} contains invalid plugins '
                    'and will not be used'.format(
                        definition['name'], schema_type
                    )
                )

        return idxs_to_pop or None

    def vaildate_definition_plugins(self, steps, definition_name, schema_type):
        '''
        Validates plugins in the given *steps* running the
        :meth:`_discover_plugin`

        *steps* : List of dictionaries with steps, stages and plugins.

        *definition_name* : Name of the current definition.

        *schema_type* : Schema type of the current definition.

        '''

        is_valid = True
        for step in steps:
            for stage in step['stages']:
                stage_name = stage['name']
                plugin_type = '{}.{}'.format(schema_type, stage_name)
                for plugin in stage['plugins']:
                    if not self._discover_plugin(plugin, plugin_type):
                        is_valid = False
                        self.logger.warning(
                            'Could not discover plugin {} of type {} for stage {}'
                            ' of the step {} in {}'.format(
                                plugin['plugin'],
                                plugin_type,
                                stage_name,
                                step['name'],
                                definition_name,
                            )
                        )
        return is_valid

    # TODO: This is discover or collect, but has to be aligned with definition name
    def _discover_plugin(self, plugin, plugin_type):
        '''
        Publish an event with the topic
        :py:const:`~ftrack_framework_core.constants.DISCOVER_PLUGIN_TOPIC`
        with the given *plugin* name and *plugin_type* as data to check that the
        pluging can be discovered with no issues.

        Returns the result of the event.

        *plugin* : Plugin definition, a dictionary with the plugin information.

        *plugin_type* : Type of plugin
        '''
        plugin_name = plugin['plugin']
        plugin_result = {}

        for host_type in reversed(self.host_types):

            # TODO: Also this registry, should probably be moved to the host, as well as we register the definitions in there.
            plugin_result = self.event_manager.publish.discover_plugin(
                plugin_name,
                plugin_type,
                host_type,
                category='plugin'
            )


            if plugin_result:
                plugin_result = plugin_result[0]
                self.logger.debug(
                    'plugin {} found for definition host_type {}'.format(
                        plugin_name, host_type
                    )
                )

                # TODO: is this really necesary? Do we need to publish the event again?

                plugin_result = self.event_manager.publish.discover_plugin(
                    plugin_name,
                    plugin_type,
                    constants.DEFAULT_STATUS,
                    host_type,
                    message='Plugin Ready'
                )

                break
            self.logger.debug(
                'plugin {} not found for definition host_type {}'.format(
                    plugin_name, host_type
                )
            )

        return plugin_result
