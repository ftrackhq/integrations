# :coding: utf-8
# :copyright: Copyright (c) 2020 ftrack

import sys
import pprint
import tempfile
import os
import shutil
import re

import platform

cwd = os.path.dirname(__file__)

sources = os.path.abspath(os.path.join(cwd, '..', 'dependencies'))

sys.path.append(sources)


import ftrack_api
import ftrack_application_launcher


#: Custom version expression to match versions `2015.5` and `2015`
#  as distinct versions.
ADOBE_VERSION_EXPRESSION = re.compile(r'(?P<version>\d[\d.]*)[^\w\d]')


class LaunchAdobeAction(ftrack_application_launcher.ApplicationLaunchAction):
    '''Adobe plugins discover and launch action.'''

    context = [None, 'Task', 'AssetVersion']
    identifier = 'ftrack-connect-launch-adobe'
    label = 'Adobe'

    def __init__(self, session, application_store, launcher):
        '''Initialise action with *applicationStore* and *launcher*.

        *applicationStore* should be an instance of
        :class:`ftrack_connect.application.ApplicationStore`.

        *launcher* should be an instance of
        :class:`ftrack_connect.application.ApplicationLauncher`.

        '''
        super(LaunchAdobeAction, self).__init__(
            session=session,
            application_store=application_store,
            launcher=launcher,
            priority=0,
        )

    def _discover(self, event):
        '''Return discovered applications.'''

        entities, event = self._translate_event(self.session, event)
        if not self.validate_selection(entities):
            return

        selection = event['data'].get('selection', [])
        items = []
        applications = self.application_store.applications
        applications = sorted(
            applications, key=lambda application: application['label']
        )

        for application in applications:
            applicationIdentifier = application['identifier']
            label = application['label']
            items.append(
                {
                    'actionIdentifier': self.identifier,
                    'label': label,
                    'variant': application.get('variant', None),
                    'description': application.get('description', None),
                    'icon': application.get('icon', 'default'),
                    'applicationIdentifier': applicationIdentifier,
                    'host': platform.node(),
                }
            )

            if selection:
                items.append(
                    {
                        'actionIdentifier': self.identifier,
                        'label': label,
                        'variant': '{variant} with latest version'.format(
                            variant=application.get('variant', '')
                        ),
                        'description': application.get('description', None),
                        'icon': application.get('icon', 'default'),
                        'launchWithLatest': True,
                        'applicationIdentifier': applicationIdentifier,
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
            self.logger.warning('No valid selection')
            return

        application_identifier = event['data']['applicationIdentifier']
        context = event['data'].copy()
        context['source'] = event['source']
        selection = context.get('selection', [])

        # If the selected entity is an asset version, change the selection
        # to parent task/shot instead since it is not possible to publish
        # to an asset version in ftrack connect.
        if entities:
            entity_type, entity_id = entities[0]
            resolved_entity = self.session.get(entity_type, entity_id)

            if selection and resolved_entity.entity_type == 'AssetVersion':
                entityId = resolved_entity.get('task_id')

                if not entityId:
                    asset = resolved_entity['asset']
                    entity = asset['parent']

                    entityId = entity['id']

                context['selection'] = [
                    {'entityId': entityId, 'entityType': 'task'}
                ]

        return self.launcher.launch(application_identifier, context)

    def get_version_information(self, event):
        '''Return version information.'''
        # Set version number to empty string since we don't know the version
        # of the plugins at the moment. Once ExManCMD is bundled with Connect
        # we can update this to return information about installed extensions.
        return [
            dict(name='ftrack connect photoshop', version='-'),
            dict(name='ftrack connect premiere', version='-'),
            dict(name='ftrack connect after effects', version='-'),
            dict(name='ftrack connect illustrator', version='-'),
        ]


class ApplicationStore(ftrack_application_launcher.ApplicationStore):
    def _discover_applications(self):
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

            applications.extend(
                self._search_filesystem(
                    expression=prefix
                    + [
                        r'Adobe Photoshop ((?:CC )?\d+)',
                        r'Adobe Photoshop ((?:CC )?\d+)\.app',
                    ],
                    label='Photoshop',
                    variant='CC {version}',
                    applicationIdentifier='photoshop_{variant}',
                    versionExpression=ADOBE_VERSION_EXPRESSION,
                    icon='photoshop',
                )
            )

            applications.extend(
                self._search_filesystem(
                    expression=prefix
                    + [
                        r'Adobe Premiere Pro ((?:CC )?\d+)',
                        r'Adobe Premiere Pro ((?:CC )?\d+)\.app',
                    ],
                    label='Premiere Pro',
                    variant='CC {version}',
                    applicationIdentifier='premiere_pro_{variant}',
                    versionExpression=ADOBE_VERSION_EXPRESSION,
                    icon='premiere',
                )
            )

            applications.extend(
                self._search_filesystem(
                    expression=prefix
                    + [
                        r'Adobe After Effects ((?:CC )?\d+)',
                        r'Adobe After Effects ((?:CC )?\d+)\.app',
                    ],
                    label='After Effects',
                    variant='CC {version}',
                    applicationIdentifier='after_effects_{variant}',
                    versionExpression=ADOBE_VERSION_EXPRESSION,
                    icon='after_effects',
                )
            )

            applications.extend(
                self._search_filesystem(
                    expression=prefix
                    + [
                        r'Adobe Illustrator ((?:CC )?\d+)',
                        r'Adobe Illustrator ?((?:CC )?\d+)?\.app',
                    ],
                    label='Illustrator',
                    variant='CC {version}',
                    applicationIdentifier='illustrator_{variant}',
                    versionExpression=ADOBE_VERSION_EXPRESSION,
                    icon='illustrator',
                )
            )

        elif sys.platform == 'win32':
            prefix = ['C:\\', 'Program Files.*']

            applications.extend(
                self._search_filesystem(
                    expression=(
                        prefix
                        + [
                            'Adobe',
                            r'Adobe Photoshop ((?:CC )?\d+)',
                            'Photoshop.exe',
                        ]
                    ),
                    label='Photoshop',
                    variant='CC {version}',
                    applicationIdentifier='photoshop_{variant}',
                    versionExpression=ADOBE_VERSION_EXPRESSION,
                    icon='photoshop',
                )
            )

            applications.extend(
                self._search_filesystem(
                    expression=(
                        prefix
                        + [
                            'Adobe',
                            r'Adobe Premiere Pro ((?:CC )?\d+)',
                            'Adobe Premiere Pro.exe',
                        ]
                    ),
                    label='Premiere Pro',
                    variant='CC {version}',
                    applicationIdentifier='premiere_pro_{variant}',
                    versionExpression=ADOBE_VERSION_EXPRESSION,
                    icon='premiere',
                )
            )

            applications.extend(
                self._search_filesystem(
                    expression=(
                        prefix
                        + [
                            'Adobe',
                            r'Adobe After Effects ((?:CC )?\d+)',
                            'Support Files',
                            'AfterFX.exe',
                        ]
                    ),
                    label='After Effects',
                    variant='CC {version}',
                    applicationIdentifier='after_effects_{variant}',
                    versionExpression=ADOBE_VERSION_EXPRESSION,
                    icon='after_effects',
                )
            )

            applications.extend(
                self._search_filesystem(
                    expression=(
                        prefix
                        + [
                            'Adobe',
                            r'Adobe Illustrator ((?:CC )?\d+)',
                            'Support Files',
                            'Contents',
                            'Windows',
                            'Illustrator.exe',
                        ]
                    ),
                    label='Illustrator',
                    variant='CC {version}',
                    applicationIdentifier='illustrator_{variant}',
                    versionExpression=ADOBE_VERSION_EXPRESSION,
                    icon='illustrator',
                )
            )

        self.logger.debug(
            'Discovered applications:\n{0}'.format(
                pprint.pformat(applications)
            )
        )

        return applications


class ApplicationLauncher(ftrack_application_launcher.ApplicationLauncher):
    application_extensions = {
        'photoshop': 'psd',
        'premiere_pro': 'prproj',
        'after_effects': 'aep',
        'illustrator': 'ai',
    }

    def _get_temporary_copy(self, filePath):
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

    def _find_latest_component(self, entityId, entityType, extension=''):
        '''Return latest published component from *entityId* and *entityType*.

        *extension* can be used to find suitable components by matching with
        their file system path.

        '''
        self.logger.debug(
            'Looking for latest version of {} {} {}'.format(
                entityId, entityType, extension
            )
        )
        if entityType == 'task':
            versions = self.session.query(
                'select components from AssetVersion where task.id is {}'.format(
                    entityId
                )
            ).all()

        elif entityType == 'assetversion':
            versions = [
                self.session.query(
                    'select components from AssetVersion where id is {}'.format(
                        entityId
                    )
                ).all()
            ]
        else:
            self.logger.debug(
                (
                    'Unable to find latest version from entityId={entityId} '
                    'with entityType={entityType}.'
                ).format(entityId=entityId, entityType=entityType)
            )
            return None

        last_date = None
        latest_component = None
        file_system_path = None

        for version in versions:
            for component in version['components']:
                avail = self.location.get_component_availability(component)
                if avail < 100:
                    continue

                file_system_path = self.location.get_filesystem_path(component)
                if file_system_path and file_system_path.endswith(extension):
                    if last_date is None or version['date'] > last_date:
                        latest_component = component
                        last_date = version['date']

        return latest_component, file_system_path

    def _get_application_launch_command(self, application, context=None):
        '''Return *application* command based on OS and *context*.

        *application* should be a mapping describing the application, as in the
        :class:`ApplicationStore`.

        *context* should provide additional information about how the
        application should be launched.

        '''
        context = context or {}

        command = super(
            ApplicationLauncher, self
        )._get_application_launch_command(application, context)

        if command is not None and context is not None:
            self.logger.debug(
                u'Launching action with context {0}'.format(
                    pprint.pformat(context)
                )
            )

            selection = context.get('selection')

            if selection and context.get('launchWithLatest', False):
                entity = selection[0]
                component = None
                file_system_path = None

                for (
                    identifier,
                    extension,
                ) in self.application_extensions.items():
                    if application['identifier'].startswith(identifier):
                        (
                            component,
                            file_system_path,
                        ) = self._find_latest_component(
                            entity['entityId'], entity['entityType'], extension
                        )
                        break

                if component is not None and file_system_path is not None:
                    file_path = self._get_temporary_copy(file_system_path)
                    self.logger.info(
                        u'Launching application with file {0!r}'.format(
                            file_path
                        )
                    )
                    command.append(file_path)
                else:
                    self.logger.warning(
                        'Unable to find an appropriate component when '
                        'launching with latest version.'
                    )

        return command


def register(session, **kw):
    '''Register hooks for Adobe plugins.'''

    if not isinstance(session, ftrack_api.session.Session):
        return

    application_store = ApplicationStore(session)

    launcher = ApplicationLauncher(application_store)

    # Create action and register to respond to discover and launch events.
    action = LaunchAdobeAction(session, application_store, launcher)
    action.register()
