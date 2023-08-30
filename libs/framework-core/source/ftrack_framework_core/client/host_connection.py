# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import logging
import copy

from ftrack_framework_core.definition import definition_object


class HostConnection(object):
    '''
    Host Connection Base class.
    This class is used to communicate between the client and the host.
    '''

    @property
    def event_manager(self):
        '''Returns instance of
        :class:`~ftrack_framework_core.event.EventManager`'''
        return self._event_manager

    @property
    def session(self):
        '''
        Returns instance of :class:`ftrack_api.session.Session`
        '''
        return self.event_manager.session

    @property
    def context_id(self):
        '''Returns the current context id fetched from the host'''
        return self._context_id

    @context_id.setter
    def context_id(self, value):
        '''
        Set the context id for this host connection to *value*.
        '''
        if value == self.context_id:
            return
        self._context_id = value
        # Every time we set context_id, we add definitions and filter them out.
        self._add_new_definitions()

    @property
    def host_id(self):
        '''Returns the current host id.'''
        return self._raw_host_data['host_id']

    @property
    def host_name(self):
        '''Returns the current host name.'''
        return self._raw_host_data['host_name']

    @property
    def context_identifiers(self):
        '''
        Find context identifiers (Based on the context id, are we in a task,
        entity type, etc...)
        '''
        if not self.context_id:
            return
        context_identifiers = []
        if self.context_id:
            entity = self.session.query(
                'TypedContext where id is {}'.format(self.context_id)
            ).first()
            if entity:
                # Task, Asset,...
                context_identifiers.append(entity.get('context_type').lower())
                if 'type' in entity:
                    # Modeling, animation...
                    context_identifiers.append(
                        entity['type'].get('name').lower()
                    )
                # Name of the task or the project
                context_identifiers.append(entity.get('name').lower())
        return context_identifiers

    @property
    def _available_filtered_host_definitions(self):
        '''Return available filtered host definitions'''
        definitions = {}
        if self.context_identifiers:
            definitions = self._filter_definitions_by_context_identifier(
                self.context_identifiers
            )
        else:
            definitions = copy.deepcopy(self._raw_host_data['definitions'])
        return definitions

    @property
    def definitions(self):
        '''Returns the discovered and filtered definitions'''
        return self._definitions

    def __del__(self):
        self.logger.debug('Closing {}'.format(self))

    def __repr__(self):
        return '<HostConnection: {}>'.format(self.host_id)

    def __hash__(self):
        return hash(self.host_id)

    def __eq__(self, other):
        return self.__hash__() == other.__hash__()

    def __init__(self, event_manager, host_data):
        '''Initialise HostConnection with instance of
        :class:`~ftrack_framework_core.event.EventManager` , and *host_data*

        *host_data* : Dictionary containing the host information.
        :py:func:`~ftrack_framework_core.host.provide_host_information`

        '''
        self.logger = logging.getLogger(
            '{0}.{1}'.format(__name__, self.__class__.__name__)
        )

        copy_data = copy.deepcopy(host_data)

        self._definitions = {}
        self._context_id = None

        self._event_manager = event_manager
        self._raw_host_data = copy_data
        self.context_id = self._raw_host_data.get('context_id')

        self.event_manager.subscribe.host_context_changed(
            self.host_id, self._on_host_context_changed_callback
        )

    def _on_host_context_changed_callback(self, event):
        '''Set the new context ID based on data provided in *event*'''
        self.context_id = event['data']['context_id']

    def _filter_definitions_by_context_identifier(self, context_identifiers):
        '''Filter *definitions* on *context_identifiers* and discoverable.'''
        result = {}
        # Filter out definitions that doesn't match the context identifiers.
        for schema_title in self._raw_host_data['definitions'].keys():
            type_result = []
            for definition in self._raw_host_data['definitions'][schema_title]:
                match = False
                discoverable = definition.get('discoverable')
                if not discoverable:
                    # Append if not discoverable, because that means should be
                    # discovered always as the Asset Manager or the logger
                    match = True
                else:
                    # This is not in a list comprehension because it needs the break
                    # once found
                    for discover_name in discoverable:
                        if discover_name.lower() in context_identifiers:
                            # Add definition as it matches
                            match = True
                            break

                if not match:
                    self.logger.debug(
                        'Excluding definition {} - context identifiers {} '
                        'does not match schema discoverable: {}.'.format(
                            definition.get('name'),
                            context_identifiers,
                            discoverable,
                        )
                    )
                if match:
                    type_result.append(definition)

            # Convert the result to definition List
            result[schema_title] = definition_object.DefinitionList(
                type_result
            )
        return copy.deepcopy(result)

    def reset_definition(self, definition_name, definition_type):
        '''
        If definition of the given *definition_type* and with the given
        *definition_name* is found, set the original values to it
        '''
        # Get the current definition
        mod_definition = self._definitions[definition_type].get_first(
            name=definition_name
        )
        # Get the original definition
        origin_definition = self._raw_host_data['definitions'][
            definition_type
        ].get_first(name=definition_name)
        if not mod_definition:
            self.logger.warning(
                'Host connection doesnt have a matching definition of type: {} '
                'and name: {} in the definitions property.'.format(
                    definition_type, definition_name
                )
            )
        if not origin_definition:
            self.logger.warning(
                'Host connection doesnt have a matching definition of type: {} '
                'and name: {} in the available definitions'.format(
                    definition_type, definition_name
                )
            )
        # Set the current definition = to the original one
        if mod_definition and origin_definition:
            # Get the index first to be able to re-set the original definition
            # in to the same position in the list
            index = self._definitions[definition_type].index(mod_definition)
            self._definitions[definition_type].pop(index)
            self._definitions[definition_type].insert(
                index, copy.deepcopy(origin_definition)
            )

    def reset_all_definitions(self):
        '''Reset all definitions to its original values sent from host'''
        self._definitions = self._available_filtered_host_definitions

    def _add_new_definitions(self):
        '''
        Add new definitions compatible with the new context,
        also purge the non-compatible ones
        '''
        if not self._available_filtered_host_definitions:
            return

        # If definitions haven't been set avoid the loops and set all available
        # definitions
        if not self._definitions:
            self._definitions = self._available_filtered_host_definitions
            return

        for schema_title in list(
            self._available_filtered_host_definitions.keys()
        ):
            # Add new definitions
            for definition in self._available_filtered_host_definitions[
                schema_title
            ]:
                if schema_title not in list(self._definitions.keys()):
                    # No schemas of that type exists in the current definitions,
                    # copy them all
                    self._definitions[
                        schema_title
                    ] = self._available_filtered_host_definitions[schema_title]
                    break
                exist = self._definitions[schema_title].get_first(
                    name=definition.name
                )
                if not exist:
                    self._definitions[schema_title].append(definition)

        for schema_title in list(self._definitions.keys()):
            # Purge not available definitions
            for definition in self._definitions.get(schema_title, []):
                if schema_title not in list(
                    self._available_filtered_host_definitions.keys()
                ):
                    # No schemas of that type exists in the available definitions,
                    # remove them all
                    self._definitions[
                        schema_title
                    ] = definition_object.DefinitionList([])
                    break
                exist = self._available_filtered_host_definitions[
                    schema_title
                ].get_first(name=definition.name)
                if not exist:
                    self._definitions[schema_title].remove(definition)
