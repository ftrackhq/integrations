# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

import getpass
import sys
import pprint
import logging

import ftrack
import ftrack_connect.application


class LaunchAction(object):
    '''Adobe plugins discover and launch action.'''

    identifier = 'ftrack-connect-launch-adobe'

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

    def isValidSelection(self, selection):
        '''Return true if the selection is valid.'''
        if (
            len(selection) != 1 or
            selection[0]['entityType'] != 'task'
        ):
            return False

        return True

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
        if not self.isValidSelection(
            event['data'].get('selection', [])
        ):
            return

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

            items.append({
                'actionIdentifier': self.identifier,
                'label': '{label} with latest version'.format(
                    label=label
                ),
                'icon': application.get('icon', 'default'),
                'launchWithLatest': True,
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
        # Prevent further processing by other listeners.
        # TODO: Only do this when actually have managed to launch a relevant
        # application.
        event.stop()

        applicationIdentifier = (
            event['data']['applicationIdentifier']
        )

        context = event['data'].copy()
        context['source'] = event['source']

        # If the selected entity is an asset version, change the selection
        # to parent task/shot instead since it is not possible to publish
        # to an asset version in ftrack connect.
        if context['selection'][0]['entityType'] == 'assetversion':
            assetVersion = ftrack.AssetVersion(
                context['selection'][0]['entityId']
            )

            entityId = assetVersion.get('taskid')

            if not entityId:
                asset = assetVersion.parent()
                entity = asset.parent()

                entityId = entity.getId()

            context['selection'] = [{
                'entityId': entityId,
                'entityType': 'task'
            }]

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
                expression=prefix + [
                    'Adobe Photoshop CC .+', 'Adobe Photoshop CC .+.app'
                ],
                label='Photoshop CC {version}',
                applicationIdentifier='photoshop_cc_{version}',
                icon='photoshop'
            ))

            applications.extend(self._searchFilesystem(
                expression=prefix + [
                    'Adobe Premiere Pro CC .+', 'Adobe Premiere Pro CC .+.app'
                ],
                label='Premiere Pro CC {version}',
                applicationIdentifier='premiere_pro_cc_{version}',
                icon='premiere'
            ))

        elif sys.platform == 'win32':
            prefix = ['C:\\', 'Program Files.*']

            applications.extend(self._searchFilesystem(
                expression=(
                    prefix +
                    ['Adobe', 'Adobe Photoshop CC .+',
                     'Photoshop.exe']
                ),
                label='Photoshop CC {version}',
                applicationIdentifier='photoshop_cc_{version}',
                icon='photoshop'
            ))

            applications.extend(self._searchFilesystem(
                expression=(
                    prefix +
                    ['Adobe', 'Adobe Premiere Pro CC .+',
                     'Adobe Premiere Pro.exe']
                ),
                label='Premiere Pro CC {version}',
                applicationIdentifier='premiere_pro_cc_{version}',
                icon='premiere'
            ))

        self.logger.debug(
            'Discovered applications:\n{0}'.format(
                pprint.pformat(applications)
            )
        )

        return applications


class ApplicationLauncher(ftrack_connect.application.ApplicationLauncher):

    def _getApplicationLaunchCommand(self, application, context=None):
        '''Return *application* command based on OS and *context*.

        *application* should be a mapping describing the application, as in the
        :class:`ApplicationStore`.

        *context* should provide additional information about how the
        application should be launched.

        '''
        command = super(
            ApplicationLauncher, self
        )._getApplicationLaunchCommand(
            application, context
        )

        # Figure out if the command should be started with the file path of
        # the latest published version.
        if command is not None and context is not None:
            selection = context.get('selection')
            if selection and context.get('launchWithLatest', False):
                entity = selection[0]
                component = None

                if application['identifier'].startswith('photoshop_cc'):
                    component = self._findLatestComponent(
                        entity['entityId'],
                        entity['entityType'],
                        'psd'
                    )

                if application['identifier'].startswith('premiere_pro_cc'):
                    component = self._findLatestComponent(
                        entity['entityId'],
                        entity['entityType'],
                        'prproj'
                    )

                if component is not None:
                    command.append(component.getFilesystemPath())

        return command


def register(registry, **kw):
    '''Register hooks for Adobe plugins.'''
    applicationStore = ApplicationStore()

    launcher = ApplicationLauncher(
        applicationStore
    )

    # Create action and register to respond to discover and launch events.
    action = LaunchAction(applicationStore, launcher)
    action.register()
