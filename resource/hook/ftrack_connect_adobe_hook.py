# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

import getpass
import sys
import pprint
import logging
import tempfile
import os
import shutil
import re

import ftrack
import ftrack_connect.application

#: Custom version expression to match versions `2015.5` and `2015`
#  as distinct versions.
ADOBE_VERSION_EXPRESSION = re.compile(
    r'(?P<version>\d[\d.]*)[^\w\d]'
)

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

        ftrack.EVENT_HUB.subscribe(
            'topic=ftrack.connect.plugin.debug-information',
            self.get_version_information
        )

    def discover(self, event):
        '''Return discovered applications.'''
        selection = event['data'].get('selection', [])
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

            if selection:
                items.append({
                    'actionIdentifier': self.identifier,
                    'label': label,
                    'variant': '{variant} with latest version'.format(
                        variant=application.get('variant', '')
                    ),
                    'description': application.get('description', None),
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
        selection = context.get('selection', [])

        # If the selected entity is an asset version, change the selection
        # to parent task/shot instead since it is not possible to publish
        # to an asset version in ftrack connect.
        if (
            selection and
            selection[0]['entityType'] == 'assetversion'
        ):
            assetVersion = ftrack.AssetVersion(
                selection[0]['entityId']
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

    def get_version_information(self, event):
        '''Return version information.'''
        # Set version number to empty string since we don't know the version
        # of the plugins at the moment. Once ExManCMD is bundled with Connect
        # we can update this to return information about installed extensions.
        return [
            dict(
                name='ftrack connect photoshop',
                version='-'
            ), dict(
                name='ftrack connect premiere',
                version='-'
            ), dict(
                name='ftrack connect after effects',
                version='-'
            )
        ]


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
                expression=prefix + [
                    'Adobe Photoshop CC .+', 'Adobe Photoshop CC .+.app'
                ],
                label='Photoshop',
                variant='CC {version}',
                applicationIdentifier='photoshop_cc_{version}',
                versionExpression=ADOBE_VERSION_EXPRESSION,
                icon='photoshop'
            ))

            applications.extend(self._searchFilesystem(
                expression=prefix + [
                    'Adobe Premiere Pro CC .+', 'Adobe Premiere Pro CC .+.app'
                ],
                label='Premiere Pro',
                variant='CC {version}',
                applicationIdentifier='premiere_pro_cc_{version}',
                versionExpression=ADOBE_VERSION_EXPRESSION,
                icon='premiere'
            ))

            applications.extend(self._searchFilesystem(
                expression=prefix + [
                    'Adobe After Effects CC .+', 'Adobe After Effects CC .+.app'
                ],
                label='After Effects',
                variant='CC {version}',
                applicationIdentifier='after_effects_cc_{version}',
                versionExpression=ADOBE_VERSION_EXPRESSION,
                icon='after_effects'
            ))

        elif sys.platform == 'win32':
            prefix = ['C:\\', 'Program Files.*']

            applications.extend(self._searchFilesystem(
                expression=(
                    prefix +
                    ['Adobe', 'Adobe Photoshop CC .+',
                     'Photoshop.exe']
                ),
                label='Photoshop',
                variant='CC {version}',
                applicationIdentifier='photoshop_cc_{version}',
                versionExpression=ADOBE_VERSION_EXPRESSION,
                icon='photoshop'
            ))

            applications.extend(self._searchFilesystem(
                expression=(
                    prefix +
                    ['Adobe', 'Adobe Premiere Pro CC .+',
                     'Adobe Premiere Pro.exe']
                ),
                label='Premiere Pro',
                variant='CC {version}',
                applicationIdentifier='premiere_pro_cc_{version}',
                versionExpression=ADOBE_VERSION_EXPRESSION,
                icon='premiere'
            ))

            applications.extend(self._searchFilesystem(
                expression=(
                    prefix +
                    ['Adobe', 'Adobe After Effects CC .+', 'Support Files',
                     'AfterFX.exe']
                ),
                label='After Effects',
                variant='CC {version}',
                applicationIdentifier='after_effects_cc_{version}',
                versionExpression=ADOBE_VERSION_EXPRESSION,
                icon='after_effects'
            ))

        self.logger.debug(
            'Discovered applications:\n{0}'.format(
                pprint.pformat(applications)
            )
        )

        return applications


class ApplicationLauncher(ftrack_connect.application.ApplicationLauncher):

    def _getTemporaryCopy(self, filePath):
        '''Copy file at *filePath* to a temporary directory and return path.

        .. note::

            The copied file does not retain the original files meta data or
            permissions.
        '''
        temporaryDirectory = tempfile.mkdtemp(prefix='ftrack_connect')
        targetPath = os.path.join(
            temporaryDirectory, os.path.basename(filePath)
        )
        shutil.copyfile(filePath, targetPath)
        return targetPath

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
            self.logger.debug(
                u'Launching action with context {0!r}'.format(context)
            )
            selection = context.get('selection')
            if selection and context.get('launchWithLatest', False):
                entity = selection[0]
                component = None

                applicationExtensions = {
                    'photoshop_cc': 'psd',
                    'premiere_pro_cc': 'prproj',
                    'after_effects_cc': 'aep'
                }

                for identifier, extension in applicationExtensions.items():
                    if application['identifier'].startswith(identifier):
                        component = self._findLatestComponent(
                            entity['entityId'],
                            entity['entityType'],
                            extension
                        )

                if component is not None:
                    filePath = self._getTemporaryCopy(
                        component.getFilesystemPath()
                    )
                    self.logger.info(
                        u'Launching application with file {0!r}'.format(
                            filePath
                        )
                    )
                    command.append(filePath)
                else:
                    self.logger.warning(
                        'Unable to find an appropriate component when '
                        'launching with latest version.'
                    )

        return command


def register(registry, **kw):
    '''Register hooks for Adobe plugins.'''

    logger = logging.getLogger(
        'ftrack_plugin:ftrack_connect_adobe_hook.register'
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

    applicationStore = ApplicationStore()

    launcher = ApplicationLauncher(
        applicationStore
    )

    # Create action and register to respond to discover and launch events.
    action = LaunchAction(applicationStore, launcher)
    action.register()
