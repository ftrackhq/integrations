'''

Import base modules and ensure the dependencies are available in the path.

'''

import sys
import os

cwd = os.path.dirname(__file__)

sources = os.path.abspath(os.path.join(cwd, '..', 'dependencies'))

sys.path.append(sources)


import ftrack_api
import ftrack_application_launcher


'''

Create launch action, to limit the context to be discovered.

'''


class LaunchAction(ftrack_application_launcher.ApplicationLaunchAction):
    context = [None, 'Task', 'Project']
    identifier = 'ftrack-connect-launch-application'
    label = 'An Application'


'''

Create application store, to let the system find the application 
versions for the various operating systems.

'''


class ApplicationStore(ftrack_application_launcher.ApplicationStore):
    def _discover_applications(self):
        applications = []

        if self.current_os == 'darwin':
            prefix = ['/', 'Applications']

            applications.extend(
                self._search_filesystem(
                    expression=prefix
                    + ['Something.*', 'Something\\d[\\w.]+.app'],
                    label='An Application',
                    variant='{version}',
                    applicationIdentifier='an-application_{variant}',
                    icon='an_application',
                    integrations={'example': ['ftrack-example-integration']},
                    launchArguments=["--arguments"],
                )
            )

        if self.current_os == 'windows':
            prefix = ['C:\\', 'Program Files.*']

            applications.extend(
                self._search_filesystem(
                    expression=prefix + ["Something.*", "Something\\d.+.exe"],
                    label='An Application',
                    variant='{version}',
                    applicationIdentifier='an-application_{variant}',
                    versionExpression="(?P<version>[\\d.]+[vabc]+[\\dvabc.]*)",
                    icon='an_application',
                    integrations={'example': ['ftrack-example-integration']},
                    launchArguments=["--arguments"],
                )
            )

        if self.current_os == 'linux':
            prefix = ["/", "usr", "local", "Something.*"]

            applications.extend(
                self._search_filesystem(
                    expression=prefix + ["Something.*", "Something\\d.+.exe"],
                    label='An Application',
                    variant='{version}',
                    applicationIdentifier='an-application_{variant}',
                    versionExpression="(?P<version>[\\d.]+[vabc]+[\\dvabc.]*)",
                    icon='an_application',
                    integrations={'example': ['ftrack-example-integration']},
                    launchArguments=["--arguments"],
                )
            )

        return applications


'''

Create application launcher, to let use the default launch action mechanism.

'''


class ApplicationLauncher(ftrack_application_launcher.ApplicationLauncher):
    '''

    This class is usually customised to provide a special launch mechanisms,
    this could involve opening a url or something completely different different.

    def launch(self, applicationIdentifier, context=None):
        [....]

        return {
            'success': success,
            'message': message
        }

    '''


'''
Register the new application launcher.
'''


def register(session, **kw):
    '''Register hooks for Adobe plugins.'''

    if not isinstance(session, ftrack_api.session.Session):
        return

    application_store = ApplicationStore(session)

    launcher = ApplicationLauncher(application_store)

    # Create action and register to respond to discover and launch events.
    action = LaunchAction(session, application_store, launcher, priority=1000)
    action.register()
