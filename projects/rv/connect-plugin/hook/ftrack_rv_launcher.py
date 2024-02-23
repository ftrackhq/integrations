# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import os
import pprint
import logging
import re
import datetime

import ftrack_api
from ftrack_connect.util import get_connect_plugin_version

from ftrack_connect.application_launcher import (
    append_path,
    ApplicationLauncher,
    ApplicationLaunchAction,
    ApplicationStore,
)

logger = logging.getLogger(__name__)

cwd = os.path.dirname(__file__)
connect_plugin_path = os.path.abspath(os.path.join(cwd, '..'))

# Read version number from __version__.py
__version__ = get_connect_plugin_version(connect_plugin_path)

python_dependencies = os.path.join(connect_plugin_path, 'dependencies')


RV_LINUX_INSTALLATION_PATH = os.getenv('RV_INSTALLATION_PATH', '/usr/local/rv')


class RvApplicationLauncher(ApplicationLauncher):
    '''Discover and launch rv.'''

    def _get_application_environment(self, application, context=None):
        '''Override to modify environment before launch.'''

        # Make sure to call super to retrieve original environment
        # which contains the selection and ftrack API.
        environment = super(
            RvApplicationLauncher, self
        )._get_application_environment(application, context)

        environment = append_path(
            python_dependencies, 'PYTHONPATH', environment
        )

        return environment


class LaunchRvAction(ApplicationLaunchAction):
    '''Adobe plugins discover and launch action.'''

    context = [None, 'Task', 'AssetVersion']
    identifier = 'ftrack-connect-launch-rv'
    label = 'rv'

    def __init__(self, session, application_store, launcher):
        '''Initialise action with *applicationStore* and *launcher*.

        *applicationStore* should be an instance of
        :class:`ftrack_connect.application.ApplicationStore`.

        *launcher* should be an instance of
        :class:`ftrack_connect.application.ApplicationLauncher`.

        '''
        super(LaunchRvAction, self).__init__(
            session=session,
            application_store=application_store,
            launcher=launcher,
            priority=0,
        )

    def _create_temp_data(self, data, expiry=None):
        if not expiry:
            expiry = datetime.datetime.now() + datetime.timedelta(hours=1)

        action = {
            'action': 'create',
            'type': 'tempdata',
            'data': data,
            'expiry': expiry,
        }

        return self.session.call(action)

    def _launch(self, event):
        '''Handle *event*.

        event['data'] should contain:

            *applicationIdentifier* to identify which application to start.

        '''
        applicationIdentifier = event['data']['applicationIdentifier']

        context = event['data'].copy()

        return self.launcher.launch(applicationIdentifier, context)


class RvApplicationStore(ApplicationStore):
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

        if self.current_os == 'darwin':
            prefix = ['/', 'Applications']
            applications.extend(
                self._search_filesystem(
                    expression=prefix + ['RV.*\.app'],
                    label='Review with RV',
                    variant='{version}',
                    applicationIdentifier='rv_{variant}_with_review',
                    icon='rv',
                    launchArguments=[
                        '--args',
                        '-flags',
                        'ModeManagerPreload=ftrack',
                    ],
                    integrations={'legacy': ['ftrack-rv']},
                )
            )

        elif self.current_os == 'windows':
            prefix = ['C:\\', 'Program Files.*']
            applications.extend(
                self._search_filesystem(
                    expression=prefix
                    + ['[Tweak|Shotgun|ShotGrid]', 'RV.\d.+', 'bin', 'rv.exe'],
                    label='Review with RV',
                    variant='{version}',
                    applicationIdentifier='rv_{variant}_with_review',
                    icon='rv',
                    launchArguments=['-flags', 'ModeManagerPreload=ftrack'],
                    versionExpression=re.compile(r'(?P<version>\d+.\d+.\d+)'),
                    integrations={'legacy': ['ftrack-rv']},
                )
            )

        elif self.current_os == 'linux':
            separator = os.path.sep
            prefix = RV_LINUX_INSTALLATION_PATH
            if not os.path.exists(RV_LINUX_INSTALLATION_PATH):
                self.logger.debug(
                    'No folder found for '
                    '$RV_INSTALLATION_PATH at : {0}'.format(
                        RV_LINUX_INSTALLATION_PATH
                    )
                )

            else:
                # Check for leading slashes
                if RV_LINUX_INSTALLATION_PATH.startswith(separator):
                    # Strip it off if does exist
                    prefix = prefix[1:]

                # Split the path in its components.
                prefix = prefix.split(separator)
                if RV_LINUX_INSTALLATION_PATH.startswith(separator):
                    # Add leading slash back
                    prefix.insert(0, separator)

                applications.extend(
                    # Detect if Centos7 or Rocky Linux 9
                    self._search_filesystem(
                        expression=prefix
                        + ['rv-centos7-x86-64-\d.+', 'bin', 'rv$'],
                        label='Review with RV',
                        variant='{version}',
                        applicationIdentifier='rv_{variant}_with_review',
                        icon='rv',
                        launchArguments=[
                            '-flags',
                            'ModeManagerPreload=ftrack',
                        ],
                        integrations={'legacy': ['ftrack-rv']},
                    )
                )

        self.logger.debug(
            'Discovered applications:\n{0}'.format(
                pprint.pformat(applications)
            )
        )

        return applications


def register(session, **kw):
    '''Register hooks.'''

    # Validate that registry is ftrack.EVENT_HANDLERS. If not, assume that
    # register is being called from a new or incompatible API and
    # return without doing anything.
    if not isinstance(session, ftrack_api.session.Session):
        return

    # Create store containing applications.
    application_store = RvApplicationStore(session)

    # Create a launcher with the store containing applications.
    launcher = RvApplicationLauncher(application_store)

    # Create action and register to respond to discover and launch actions.
    action = LaunchRvAction(session, application_store, launcher)
    action.register()

    logger.info('Registered rv launcher v{}.'.format(__version__))
