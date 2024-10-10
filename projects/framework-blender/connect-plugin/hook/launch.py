import logging

import ftrack_api

import os
import sys
import pprint
import appdirs
import platform
import ftrack_connect.application_launcher

# Cache dependencies path in an environment variable
# so we can apply to Blender after launch.
#
# Blender uses an internal Python sys module, not the system one
cwd = os.path.dirname(__file__)
sources = os.path.abspath(os.path.join(cwd, '..', 'dependencies'))
ftrack_connect_blender_resource_path = os.path.abspath(os.path.join(cwd, '..', 'resource'))
os.environ["FTRACK_SYSPATH"] = sources



class ApplicationStore(ftrack_connect.application_launcher.ApplicationStore):
    '''Store used to find and keep track of available applications.'''

    def _discover_applications(self):
        '''Return a list of applications that can be launched from this host.'''
        applications = []

        if self.current_os == 'darwin':
            prefix = ['/', 'Applications']

            applications.extend(self._search_filesystem(
                expression=prefix + [
                    'Blender*', 'Blender.app'
                ],
                label='Blender',
                variant='{version}',
                applicationIdentifier='blender_{variant}'
            ))

        elif self.current_os == 'windows':
            prefix = ['C:\\', 'Program Files.*']

            applications.extend(self._search_filesystem(
                expression=(
                        prefix +
                        ['Blender Foundation', 'Blender*', 'blender.exe']
                ),
                label='Blender',
                variant='{version}',
                applicationIdentifier='blender_{variant}'
            ))

        self.logger.debug(
            'Discovered applications:\n{0}'.format(
                pprint.pformat(applications)
            )
        )

        return applications


class BlenderAction(ftrack_connect.application_launcher.ApplicationLaunchAction):
    '''Launch Blender action.'''
    context = ['Task']
    label = 'blender launcher'
    identifier = 'blender-launch-action'

    def __init__(
        self, session, application_store, launcher, priority
    ):
        super(BlenderAction, self).__init__(session, application_store, launcher, priority)

    def __get_addons_path(self, version):
        if sys.platform == 'darwin':
            roaming = False
        elif sys.platform == 'win32':
            roaming = True

        return os.path.join(
            appdirs.user_data_dir('Blender', 'Blender Foundation', roaming=roaming),
            version,
            'scripts',
            'addons',
            ''
        )

    def ensure_addon_folder(self, version):
        addon_directory = self.__get_addons_path(version)
        if not os.path.exists(addon_directory):
            os.makedirs(addon_directory)

    def register(self, session):
        '''Register action.'''
        session.event_hub.subscribe(
            'topic=ftrack.action.discover',
            self.discover
        )

        session.event_hub.subscribe(
            'topic=ftrack.action.launch and data.actionIdentifier={0}'.format(
                self.identifier
            ),
            self.launch
        )

    def is_component(self, selection):
        if (
                len(selection) != 1 or
                selection[0]['entityType'] != 'Component'
        ):
            return False

        return True

    def discover(self, event):
        '''Return action based on *event*.'''

        launchArguments = []

        selection = event['data'].get('selection', [])

        # Add config file to launch arguments
        launchArguments.extend([
            '--python',
            os.path.join(ftrack_connect_blender_resource_path, 'bootstrap', 'init.py')
        ])

        items = []
        applications = self.application_store.applications
        applications = sorted(
            applications, key=lambda application: application['label']
        )

        for application in applications:
            applicationIdentifier = application['identifier']
            label = application['label']

            context = event['data'].copy()
            context['source'] = event['source']


            items.append(
                {
                    'actionIdentifier': self.identifier,
                    'label': label,
                    'icon': application.get('icon', 'default'),
                    'variant': application.get('variant', None),
                    'applicationIdentifier': applicationIdentifier,
                    'integrations': application.get('integrations', {}),
                    'host': platform.node(),
                    'launchArguments': launchArguments,
                }

            )

        return {
            'items': items
        }

    def launch(self, event):
        '''Callback method for Blender action.'''
        applicationIdentifier = (
            event['data']['applicationIdentifier']
        )

        self.ensure_addon_folder(
            event['data']['variant']
        )

        context = event['data'].copy()

        return self.launcher.launch(
            applicationIdentifier, context
        )


class ApplicationLauncher(ftrack_connect.application_launcher.ApplicationLauncher):
    '''Custom launcher to modify environment before launch.'''

    def _get_application_launch_command(self, application, context=None):
        command = super(ApplicationLauncher, self)._get_application_launch_command(application, context)
        command.extend(context.get('launchArguments'))
        return command


def register(session, **kw):
    '''Register action in Connect.'''

    # Validate that session is an instance of ftrack_api.Session. If not, assume
    # that register is being called from an old or incompatible API and return
    # without doing anything.
    if not isinstance(session, ftrack_api.Session):
        return

    applicationStore = ApplicationStore(session)

    launcher = ApplicationLauncher(
        applicationStore
    )

    action = BlenderAction(session, applicationStore, launcher, priority=1000)
    action.register(session)