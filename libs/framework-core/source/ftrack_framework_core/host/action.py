# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import copy
import sys
import logging
import platform

from ftrack_action_handler.action import BaseAction


class ToolAction(BaseAction):
    @property
    def tool_config(self):
        '''Return convenient exposure of the self._tool_config reference.'''
        return self._tool_config

    @property
    def host(self):
        '''Return convenient exposure of the host attribute.'''
        return self._host

    def __init__(self, host, session, tool_config, priority=sys.maxsize):
        self.label = tool_config['name']
        self.identifier = f'{tool_config["name"]}-launch'

        super(ToolAction, self).__init__(session)

        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )

        self.priority = priority
        self._tool_config = tool_config
        self._host = host

    def validate_selection(self, entities):
        '''Return True if the selection is valid.

        Utility method to check *entities* validity.

        '''
        if not entities:
            return False

        entity_type, entity_id = entities[0]
        resolved_entity = self.session.get(entity_type, entity_id)

        print(f'@@@  resolved_entity_type: {resolved_entity}')

        # Check if compatible with tool config
        if 'entity_type' not in self.tool_config:
            self.logger.warning(
                f'Tool config {self.tool_config} does not have entity_type defined!'
            )
            return False

        if (
            resolved_entity.entity_type.lower()
            != self.tool_config['entity_type'].lower()
        ):
            self.logger.warning(
                f'Entity type {resolved_entity.entity_type} is not compatible with tool config {self.tool_config}'
            )
            return False

        return True

    def _discover(self, event):
        entities, event = self._translate_event(self.session, event)

        if not self.validate_selection(entities):
            return

        items = []

        items.append(
            {
                'label': self.tool_config['name'],
                'actionIdentifier': self.identifier,
                'host': platform.node(),
                'icon': 'nuke',
            }
        )

        return {'items': items}

    def _launch(self, event):
        '''Handle *event*.

        event['data'] should contain:

            *applicationIdentifier* to identify which application to start.

        '''
        event.stop()

        entities, event = self._translate_event(self.session, event)

        if not self.validate_selection(entities):
            return

        processed = 0
        for entity_type, entity_id in entities:
            component = self.session.get(entity_type, entity_id)
            version = component['version']

            # Clone the tool config
            tool_config = copy.deepcopy(self.tool_config)

            import json

            print(json.dumps(tool_config, indent=4))

            location = self.session.pick_location()
            component_path = location.get_filesystem_path(component)

            # Inject the component_path
            plugin = None
            for plugin in tool_config['engine']:
                if plugin['plugin'] == 'nuke_movie_loader':
                    break
            print(f'plugin: {plugin}')
            # plugin = self.host.registry.get_one(name='component_path_collector')
            tool_config_options = {}
            tool_config_options[plugin['reference']] = {
                'asset_version_id': version['id'],
                'component': component['name'],
                'collected_path': component_path,
            }

            # Tun the tool config
            self.host.event_manager.publish.host_run_tool_config(
                self.host.id,
                tool_config['reference'],
                tool_config_options,
            )

        return {
            'success': True,
            'message': (f'Successfully processed {processed} entities'),
        }

    def register(self):
        '''Register discover actions on logged in user.'''

        self.session.event_hub.subscribe(
            'topic=ftrack.action.discover '
            'and source.user.username={0}'.format(self.session.api_user),
            self._discover,
            priority=self.priority,
        )

        self.session.event_hub.subscribe(
            'topic=ftrack.action.launch '
            'and source.user.username={0} '
            'and data.actionIdentifier={1} '
            'and data.host={2}'.format(
                self.session.api_user, self.identifier, platform.node()
            ),
            self._launch,
            priority=self.priority,
        )
