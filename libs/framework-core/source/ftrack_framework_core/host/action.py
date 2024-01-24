# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import sys
import logging
import platform

from ftrack_action_handler.action import BaseAction


class ToolAction(BaseAction):
    context = []

    @property
    def tool_config(self):
        '''Return convenient exposure of the self._tool_config reference.'''
        return self._tool_config

    @property
    def session(self):
        '''Return convenient exposure of the self._session reference.'''
        return self._session

    def __init__(self, session, tool_config, priority=sys.maxsize):
        super(ToolAction, self).__init__(session)

        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )

        self.priority = priority
        self._tool_config = tool_config

    def validate_selection(self, entities):
        '''Return True if the selection is valid.

        Utility method to check *entities* validity.

        '''
        if not self.context:
            raise ValueError('No valid context type set for discovery')

        if not entities and None in self.context:
            # handle non context discovery
            return True

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
                'host': platform.node(),
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

        application_identifier = event['data']['applicationIdentifier']
        context = event['data'].copy()
        context['source'] = event['source']

        return self.launcher.launch(application_identifier, context)

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
