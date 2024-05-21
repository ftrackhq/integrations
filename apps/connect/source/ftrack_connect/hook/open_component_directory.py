# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import logging
import os

import platform
import ftrack_api
from ftrack_connect.utils.directory import open_directory


class OpenComponentDirectoryAction(object):
    '''Action to open a component directory in os file browser.'''

    identifier = 'ftrack-connect-open-component-directory'

    failed = {
        'success': False,
        'message': ('Could not open component directory.'),
    }

    def __init__(self, session, logger):
        '''Instantiate action with *session*.'''
        self.session = session
        self.logger = logger
        self.node = platform.node()

    def discover(self, event):
        '''Discover *event*.'''
        selection = event['data'].get('selection', [])
        if len(selection) == 1 and selection[0]['entityType'] == 'Component':
            return {
                'items': [
                    {
                        'label': 'Open directory',
                        'actionIdentifier': self.identifier,
                        'host': self.node,
                    }
                ]
            }

    def resolve_path(self, component_id):
        '''Return path from *component_id*.'''

        location = None
        component = None
        try:
            component = self.session.get('Component', component_id)
            location = self.session.pick_location(component)
        except Exception:
            self.logger.exception(
                'Could not pick location for component {0!r}'.format(component)
            )

        path = None
        if location:
            try:
                path = location.get_filesystem_path(component)
            except ftrack_api.exception.AccessorUnsupportedOperationError:
                self.logger.warn(
                    'Component {0!r} does not support filesystem access for '
                    '{1!r}'.format(component, location)
                )
            self.logger.info('Location is only in api: {0!r}'.format(location))
        return path

    def launch(self, event):
        '''Launch action for *event*.'''
        selection = event['data']['selection'][0]

        if selection['entityType'] != 'Component':
            return

        path = None
        component_id = selection['entityId']
        try:
            path = self.resolve_path(component_id)
        except Exception:
            self.logger.exception(
                'Exception raised while resolving component with id '
                '{0!r}'.format(component_id)
            )

        if path is None:
            self.logger.info(
                'Could not determine a valid file system path for: '
                '{0!r}'.format(component_id)
            )
            return self.failed

        if os.path.exists(path):
            # File or directory exists.
            open_directory(path)
        elif os.path.exists(os.path.dirname(path)):
            # Handle cases where file system path is a sequence expression.
            open_directory(os.path.dirname(path))
        else:
            # No file, directory or parent directory exists for path.
            self.logger.info(
                'Directory resolved but non-existing {0!r} and {1!r}:'
                '{0!r}'.format(component_id, path)
            )
            return self.failed

        return {
            'success': True,
            'message': 'Successfully opened component directory.',
        }

    def register(self):
        '''Register to event hub.'''
        self.session.event_hub.subscribe(
            u'topic=ftrack.action.discover and '
            u'source.user.username="{0}"'.format(self.session.api_user),
            self.discover,
        )

        self.session.event_hub.subscribe(
            u'topic=ftrack.action.launch and '
            u'data.actionIdentifier={0} and '
            u'source.user.username="{1}" and '
            u'data.host={2}'.format(
                self.identifier, self.session.api_user, self.node
            ),
            self.launch,
        )


def register(session, **kw):
    '''Register hooks.'''

    logger = logging.getLogger('ftrack_connect:open-component-directory')

    # Validate that session is an instance of ftrack_api.session.Session. If
    # not, assume that register is being called from an old or incompatible API
    # and return without doing anything.
    if not isinstance(session, ftrack_api.Session):
        logger.debug(
            'Not subscribing plugin as passed argument {0!r} is not an '
            'Session instance.'.format(session)
        )
        return

    action = OpenComponentDirectoryAction(session, logger)
    action.register()
