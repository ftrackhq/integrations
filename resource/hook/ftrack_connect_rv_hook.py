# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

import os
import getpass
import sys
import pprint
import logging
import json
import re

import ftrack
import ftrack_connect.application


try:
    import ftrack_connect_rv
except ImportError:
    dependencies_path = os.path.realpath(
        os.path.join(os.path.dirname(__file__), '..', 'package')
    )
    sys.path.append(dependencies_path)
    import ftrack_connect_rv


class ApplicationLauncher(ftrack_connect.application.ApplicationLauncher):
    '''Discover and launch rv.'''

    def _getApplicationEnvironment(self, application, context=None):
        '''Override to modify environment before launch.'''

        # Make sure to call super to retrieve original environment
        # which contains the selection and ftrack API.
        environment = super(
            ApplicationLauncher, self
        )._getApplicationEnvironment(application, context)

        MU_MODULE_PATH = os.path.join(
            os.path.dirname(ftrack_connect_rv.__file__),
            '..', 'resource', 'plugin', 'Package'
        )

        environment = ftrack_connect.application.appendPath(
            MU_MODULE_PATH,
            'MU_MODULE_PATH',
            environment
        )

        PYTHONPATH = os.path.join(
            os.path.dirname(ftrack_connect_rv.__file__),
            '..', 'package'
        )

        environment = ftrack_connect.application.appendPath(
            PYTHONPATH,
            'PYTHONPATH',
            environment
        )

        return environment


class LaunchApplicationAction(object):
    '''Discover and launch action.'''

    identifier = 'ftrack-connect-launch-rv'

    def __init__(self, applicationStore, launcher):
        '''Initialise action with *applicationStore* and *launcher*.

        *applicationStore* should be an instance of
        :class:`ftrack_connect.application.ApplicationStore`.

        *launcher* should be an instance of
        :class:`ftrack_connect.application.ApplicationLauncher`.

        '''
        super(LaunchApplicationAction, self).__init__()

        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )

        self.applicationStore = applicationStore
        self.launcher = launcher

    def _createPlaylistFromSelection(self, selection):
        '''Return new selection with temporary playlist from *selection*.'''

        # If selection is only one entity we don't need to create
        # a playlist.
        if len(selection) == 1:
            return selection

        playlist = []
        for entity in selection:
            playlist.append({
                'id': entity['entityId'],
                'type': entity['entityType']
            })

        playlist = ftrack.createTempData(json.dumps(playlist))

        selection = [{
            'entityType': 'tempdata',
            'entityId': playlist.getId()
        }]

        return selection

    def register(self):
        '''Register discover actions on logged in user.'''
        ftrack.EVENT_HUB.subscribe(
            'topic=ftrack.action.discover and source.user.username={0}'.format(
                getpass.getuser()
            ),
            self.discover
        )

        ftrack.EVENT_HUB.subscribe(
            'topic=ftrack.action.launch and source.user.username={0} '
            'and data.actionIdentifier={1}'.format(
                getpass.getuser(), self.identifier
            ),
            self.launch
        )

        ftrack.EVENT_HUB.subscribe(
            'topic=ftrack.connect.plugin.debug-information',
            self.get_version_information
        )

    def discover(self, event):
        '''Return discovered applications.'''
        items = []
        applications = self.applicationStore.applications
        applications = sorted(
            applications, key=lambda application: application['label']
        )

        for application in applications:
            applicationIdentifier = application['identifier']
            label = application['label']
            items.append({
                'actionIdentifier': self.identifier,
                'label': label,
                'variant': application.get('variant', None),
                'description': application.get('description', None),
                'icon': application.get('icon', 'default'),
                'applicationIdentifier': applicationIdentifier
            })

        return {
            'items': items
        }

    def launch(self, event):
        '''Handle *event*.

        event['data'] should contain:

            *applicationIdentifier* to identify which application to start.

        '''
        applicationIdentifier = (
            event['data']['applicationIdentifier']
        )

        context = event['data'].copy()

        # Rewrite original selection to a playlist.
        context['selection'] = self._createPlaylistFromSelection(
            context['selection']
        )

        return self.launcher.launch(
            applicationIdentifier, context
        )

    def get_version_information(self, event):
        '''Return version information.'''
        return dict(
            name='ftrack connect rv',
            version=ftrack_connect_rv.__version__
        )


class ApplicationStore(ftrack_connect.application.ApplicationStore):

    def _discoverApplications(self):
        '''Return a list of applications that can be launched from this host.

        An application should be of the form:

            dict(
                'identifier': 'name_version',
                'label': 'Name',
                'variant': 'version',
                'description': 'description',
                'path': 'Absolute path to the file',
                'version': 'Version of the application',
                'icon': 'URL or name of predefined icon'
            )

        '''
        applications = []

        if sys.platform == 'darwin':
            prefix = ['/', 'Applications']

            applications.extend(self._searchFilesystem(
                expression=prefix + ['RV.\d+.app'],
                label='Review with RV',
                variant='{version}',
                applicationIdentifier='rv_{version}_with_review',
                icon='rv',
                launchArguments=[
                    '--args', '-flags', 'ModeManagerPreload=ftrack'
                ]
            ))

        elif sys.platform == 'win32':
            prefix = ['C:\\', 'Program Files.*']

            applications.extend(self._searchFilesystem(
                expression=prefix + [
                    'Tweak', 'RV.\d.+', 'bin', 'rv.exe'
                ],
                label='Review with RV',
                variant='{version}',
                applicationIdentifier='rv_{version}_with_review',
                icon='rv',
                launchArguments=[
                    '-flags', 'ModeManagerPreload=ftrack'
                ],
                versionExpression=re.compile(
                    r'(?P<version>\d+.\d+.\d+)'
                )
            ))

        self.logger.debug(
            'Discovered applications:\n{0}'.format(
                pprint.pformat(applications)
            )
        )

        return applications


def register(registry, **kw):
    '''Register hooks.'''

    logger = logging.getLogger(
        'ftrack_plugin:ftrack_connect_rv_hook.register'
    )

    # Validate that registry is an instance of ftrack.Registry. If not,
    # assume that register is being called from a new or incompatible API and
    # return without doing anything.
    if not isinstance(registry, ftrack.Registry):
        logger.debug(
            'Not subscribing plugin as passed argument {0!r} is not an '
            'ftrack.Registry instance.'.format(registry)
        )
        return

    # Create store containing applications.
    applicationStore = ApplicationStore()

    # Create a launcher with the store containing applications.
    launcher = ApplicationLauncher(
        applicationStore
    )

    # Create action and register to respond to discover and launch actions.
    action = LaunchApplicationAction(applicationStore, launcher)
    action.register()
