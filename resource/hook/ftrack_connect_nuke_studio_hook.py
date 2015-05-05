# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

import os
import getpass
import sys
import pprint
import logging

import ftrack
import ftrack_connect.application

FTRACK_CONNECT_NUKE_STUDIO_PATH = os.environ.get(
    'FTRACK_CONNECT_NUKE_STUDIO_PATH',
    os.path.abspath(
        os.path.join(
            os.path.dirname(__file__), '..', 'nuke_studio'
        )
    )
)


class LaunchAction(object):
    '''ftrack connect nuke studio discover and launch action.'''

    identifier = 'ftrack-connect-launch-nuke-studio'

    def __init__(self, applicationStore, launcher):
        '''Initialise action with *applicationStore* and *launcher*.

        *applicationStore* should be an instance of
        :class:`ftrack_connect.application.ApplicationStore`.

        *launcher* should be an instance of
        :class:`ftrack_connect.application.ApplicationLauncher`.

        '''
        super(LaunchAction, self).__init__()

        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )

        self.applicationStore = applicationStore
        self.launcher = launcher

    def register(self):
        '''Override register to filter discover actions on logged in user.'''
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
                'icon': application.get('icon', 'default'),
                'applicationIdentifier': applicationIdentifier
            })

        return {
            'items': items
        }

    def launch(self, event):
        '''Handle launch *event*.'''
        applicationIdentifier = (
            event['data']['applicationIdentifier']
        )

        context = event['data'].copy()
        context['source'] = event['source']

        applicationIdentifier = event['data']['applicationIdentifier']
        context = event['data'].copy()
        context['source'] = event['source']

        return self.launcher.launch(
            applicationIdentifier, context
        )


class ApplicationStore(ftrack_connect.application.ApplicationStore):

    def _discoverApplications(self):
        '''Return a list of applications that can be launched from this host.

        An application should be of the form:

            dict(
                'identifier': 'name_version',
                'label': 'Name version',
                'path': 'Absolute path to the file',
                'version': 'Version of the application',
                'icon': 'URL or name of predefined icon'
            )

        '''
        applications = []

        if sys.platform == 'darwin':
            prefix = ['/', 'Applications']

            applications.extend(self._searchFilesystem(
                expression=prefix + ['Nuke.*', 'NukeStudio\d[\w.]+.app'],
                label='Nuke Studio {version}',
                applicationIdentifier='nuke_studio_{version}',
                icon='nuke_studio'
            ))

        elif sys.platform == 'win32':
            prefix = ['C:\\', 'Program Files.*']

            applications.extend(self._searchFilesystem(
                expression=prefix + ['Nuke.*', 'Nuke\d.+.exe'],
                label='Nuke Studio {version}',
                applicationIdentifier='nuke_studio_{version}',
                icon='nuke_studio',
                launchArguments=['--studio']
            ))

        elif sys.platform == 'linux2':

            applications.extend(self._searchFilesystem(
                expression=['/', 'usr', 'local', 'Nuke.*', 'Nuke\d.+'],
                label='Nuke Studio {version}',
                applicationIdentifier='nuke_studio_{version}',
                icon='nuke_studio',
                launchArguments=['--studio']
            ))

        self.logger.debug(
            'Discovered applications:\n{0}'.format(
                pprint.pformat(applications)
            )
        )

        return applications


class ApplicationLauncher(ftrack_connect.application.ApplicationLauncher):
    '''Launch nuke studio.'''

    def _getApplicationEnvironment(self, application, context):
        '''Modify and return environment with nuke studio added.'''
        environment = super(
            ApplicationLauncher, self
        )._getApplicationEnvironment(
            application, context
        )

        environment['NUKE_PATH'] = os.path.join(
            FTRACK_CONNECT_NUKE_STUDIO_PATH, 'hiero', 'nuke'
        )

        environment['FOUNDRY_ASSET_PLUGIN_PATH'] = os.path.join(
            FTRACK_CONNECT_NUKE_STUDIO_PATH, 'hiero'
        )
        environment['FTRACK_NUKE_STUDIO_CONFIG'] = os.path.join(
            FTRACK_CONNECT_NUKE_STUDIO_PATH, 'config.json'
        )
        environment['FTRACK_PROCESSOR_PLUGIN_PATH'] = os.path.join(
            FTRACK_CONNECT_NUKE_STUDIO_PATH, 'processor'
        )

        # Set the FTRACK_EVENT_PLUGIN_PATH to include the notification callback
        # hooks.
        environment = ftrack_connect.application.appendPath(
            os.path.join(
                FTRACK_CONNECT_NUKE_STUDIO_PATH, 'crew_hook'
            ), 'FTRACK_EVENT_PLUGIN_PATH', environment
        )

        environment = ftrack_connect.application.appendPath(
            os.path.join(
                FTRACK_CONNECT_NUKE_STUDIO_PATH, '..',
                'ftrack_python_api'
            ), 'FTRACK_PYTHON_API_PLUGIN_PATH', environment
        )

        environment['NUKE_USE_FNASSETAPI'] = '1'

        return environment


def register(registry, **kw):
    '''Register hooks for ftrack connect legacy plugins.'''
    applicationStore = ApplicationStore()

    launcher = ApplicationLauncher(applicationStore)

    # Create action and register to respond to discover and launch events.
    action = LaunchAction(applicationStore, launcher)
    action.register()
