# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import logging
import copy

from ftrack_utils.framework.config.tool import get_tool_config_by_name


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
        self._check_context_identifiers()
        # Every time we set context_id, we add tool_configs and filter them out.
        self._add_new_tool_configs()

    @property
    def host_id(self):
        '''Returns the current host id.'''
        return self._raw_host_data['host_id']

    @property
    def context_identifiers(self):
        '''
        Return context identifiers
        '''
        return self._context_identifiers

    @property
    def _available_filtered_host_tool_configs(self):
        '''Return available filtered host tool_configs'''
        tool_configs = {}
        if self.context_identifiers:
            tool_configs = self._filter_tool_configs_by_context_identifier(
                self.context_identifiers
            )
        else:
            tool_configs = copy.deepcopy(self._raw_host_data['tool_configs'])
        return tool_configs

    @property
    def tool_configs(self):
        '''Returns the discovered and filtered tool_configs'''
        return self._tool_configs

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

        self._tool_configs = {}
        self._context_id = None
        self._context_identifiers = []

        self._event_manager = event_manager
        self._raw_host_data = copy_data
        self.context_id = self._raw_host_data.get('context_id')

        self.event_manager.subscribe.host_context_changed(
            self.host_id, self._on_host_context_changed_callback
        )

    def _on_host_context_changed_callback(self, event):
        '''Set the new context ID based on data provided in *event*'''
        self.context_id = event['data']['context_id']

    def _check_context_identifiers(self):
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
        self._context_identifiers = context_identifiers
        return context_identifiers

    def _filter_tool_configs_by_context_identifier(self, context_identifiers):
        '''Filter *tool_configs* on *context_identifiers* and discoverable.'''
        result = {}
        # Filter out tool_configs that doesn't match the context identifiers.
        for schema_title in self._raw_host_data['tool_configs'].keys():
            type_result = []
            for tool_config in self._raw_host_data['tool_configs'][
                schema_title
            ]:
                match = False
                discoverable = tool_config.get('discoverable')
                if not discoverable:
                    # Append if not discoverable, because that means should be
                    # discovered always as the Asset Manager or the logger
                    match = True
                else:
                    # This is not in a list comprehension because it needs the break
                    # once found
                    for discover_name in discoverable:
                        if discover_name.lower() in context_identifiers:
                            # Add tool_config as it matches
                            match = True
                            break

                if not match:
                    self.logger.debug(
                        'Excluding tool_config {} - context identifiers {} '
                        'does not match schema discoverable: {}.'.format(
                            tool_config.get('tool_title'),
                            context_identifiers,
                            discoverable,
                        )
                    )
                if match:
                    type_result.append(tool_config)

            # Convert the result to tool_config List
            result[schema_title] = type_result
        return copy.deepcopy(result)

    def _add_new_tool_configs(self):
        '''
        Add new tool_configs compatible with the new context,
        also purge the non-compatible ones
        '''
        if not self._available_filtered_host_tool_configs:
            return

        # If tool_configs haven't been set avoid the loops and set all available
        # tool_configs
        if not self._tool_configs:
            self._tool_configs = self._available_filtered_host_tool_configs
            return

        for config_type in list(
            self._available_filtered_host_tool_configs.keys()
        ):
            # Add new tool_configs
            for tool_config in self._available_filtered_host_tool_configs[
                config_type
            ]:
                if config_type not in list(self._tool_configs.keys()):
                    # No config_type of that type exists in the current tool_configs,
                    # copy them all
                    self._tool_configs[
                        config_type
                    ] = self._available_filtered_host_tool_configs[config_type]
                    break
                # If the new one is not in the current names, add it.
                exist = get_tool_config_by_name(
                    self._tool_configs[config_type], tool_config['name']
                )
                if not exist:
                    self._tool_configs[config_type].append(tool_config)

        for config_type in list(self._tool_configs.keys()):
            # Purge not available tool_configs
            for tool_config in self._tool_configs.get(config_type, []):
                if config_type not in list(
                    self._available_filtered_host_tool_configs.keys()
                ):
                    # No tool-configs of that type exists in the available
                    # tool_configs, remove them all
                    self._tool_configs[config_type] = []
                    break
                exist = get_tool_config_by_name(
                    self._available_filtered_host_tool_configs[config_type],
                    tool_config['name'],
                )
                if not exist:
                    self._tool_configs[config_type].remove(tool_config)

    def reset_all_tool_configs(self):
        '''Reset all tool_configs to its original values sent from host'''
        self._tool_configs = self._available_filtered_host_tool_configs
