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

    @property
    def host_id(self):
        '''Returns the current host id.'''
        return self._raw_host_data['host_id']

    @property
    def host_name(self):
        '''Returns the current host name.'''
        return self._raw_host_data['host_name']

    @property
    def definitions(self):
        '''Returns the discovered and filtered definitions'''
        context_identifiers = []
        # Find context identifiers (Based on the context id, are we in a task,
        # entity type, etc...)
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

        if context_identifiers:
            result = {}
            # Filter definitions that doesn't match the context identifiers.
            for schema_title in self._raw_host_data['definitions'].keys():
                result[schema_title] = self._filter_definitions(
                    context_identifiers,
                    self._raw_host_data['definitions'][schema_title],
                )
            return copy.deepcopy(result)

        return self._raw_host_data['definitions']

    def _filter_definitions(self, context_identifiers, definitions):
        '''Filter *definitions* on *context_identifiers* and discoverable.'''
        result = []
        for definition in definitions:
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
                result.append(definition)

        # Convert the result to definition List
        return definition_object.DefinitionList(result)

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

        self._event_manager = event_manager
        self._raw_host_data = copy_data
        self._context_id = self._raw_host_data.get('context_id')

        self.event_manager.subscribe.host_context_changed(
            self.host_id, self._on_host_context_changed_callback
        )

    def _on_host_context_changed_callback(self, event):
        '''Set the new context ID based on data provided in *event*'''
        self.context_id = event['data']['context_id']
