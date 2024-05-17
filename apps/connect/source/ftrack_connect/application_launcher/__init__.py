# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import plistlib
import sys
import re
import ssl
import tempfile
import subprocess
import collections
import base64
import json
import logging
import platform
from operator import itemgetter
from distutils.version import LooseVersion
import os

if sys.version_info.major == 3 and sys.version_info.minor >= 10:
    from collections.abc import MutableMapping, Mapping
else:
    from collections import MutableMapping, Mapping

import ftrack_api
from ftrack_action_handler.action import BaseAction
from ftrack_utils.usage import get_usage_tracker


#: Default expression to match version component of executable path.
#: Will match last set of numbers in string where numbers may contain a digit
#: followed by zero or more digits, periods, or the letters 'a', 'b', 'c' or 'v'
#: E.g. /path/to/x86/some/application/folder/v1.8v2b1/app.exe -> 1.8v2b1
DEFAULT_VERSION_EXPRESSION = re.compile(r'(?P<version>\d[\d.vabc]*?)[^\d]*$')

AVAILABLE_ICONS = {
    'hiero': '/application_icons/hiero.png',
    'hieroplayer': '/application_icons/hieroplayer.png',
    'nukex': '/application_icons/nukex.png',
    'nuke': '/application_icons/nuke.png',
    'nuke_studio': '/application_icons/nuke_studio.png',
    'premiere': '/application_icons/premiere.png',
    'maya': '/application_icons/maya.png',
    'cinesync': '/application_icons/cinesync.png',
    'photoshop': '/application_icons/photoshop.png',
    'prelude': '/application_icons/prelude.png',
    'after_effects': '/application_icons/after_effects.png',
    '3ds_max': '/application_icons/3ds_max.png',
    'cinema_4d': '/application_icons/cinema_4d.png',
    'indesign': '/application_icons/indesign.png',
    'illustrator': '/application_icons/illustrator.png',
    'houdini': '/application_icons/houdini.png',
    'unreal-engine': '/application_icons/unreal_engine.png',
    'unity': '/application_icons/unity.png',
    'rv': '/application_icons/rv.png',
    'harmony': '/application_icons/harmony.png',
}


def prepend_path(path, key, environment):
    '''Prepend *path* to *key* in *environment*.'''
    try:
        environment[key] = os.pathsep.join([path, environment[key]])
    except KeyError:
        environment[key] = path

    return environment


def append_path(path, key, environment):
    '''Append *path* to *key* in *environment*.'''
    try:
        environment[key] = os.pathsep.join([environment[key], path])
    except KeyError:
        environment[key] = path

    return environment


def pop_path(path, key, environment):
    '''Remove *path* to *key* in *environment*.'''
    env_paths = environment.get(key)
    if env_paths:
        environment[key] = os.pathsep.join(
            [
                existing_path
                for existing_path in env_paths.split(os.pathsep)
                if existing_path.replace('\\', '/') != path.replace('\\', '/')
            ]
        )


class ApplicationStore(object):
    '''Discover and store available applications on this host.'''

    @property
    def current_os(self):
        return platform.system().lower()

    @property
    def session(self):
        '''Return current session.'''
        return self._session

    def __init__(self, session):
        '''Instantiate store and discover applications.'''
        super(ApplicationStore, self).__init__()

        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )

        self._session = session

        # Discover applications and store.
        self.applications = self._discover_applications()

    def get_application(self, identifier):
        '''Return first application with matching *identifier*.

        *identifier* may contain a wildcard at the end to match the first
        substring matching entry.

        Return None if no application matches.

        '''
        hasWildcard = identifier[-1] == '*'
        if hasWildcard:
            identifier = identifier[:-1]

        for application in self.applications:
            if hasWildcard:
                if application['identifier'].startswith(identifier):
                    return application
            else:
                if application['identifier'] == identifier:
                    return application

        return None

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

        elif self.current_os == 'windows':
            prefix = ['C:\\', 'Program Files.*']

        return applications

    def _get_icon_url(self, icon_name):
        result = icon_name
        icon_url = AVAILABLE_ICONS.get(icon_name)
        if icon_url:
            result = '{}{}'.format(self.session.server_url, icon_url)

        return result

    def _conditional_expand_extension_path(self, value, connect_plugin_path):
        '''Convert extension path *value*  - support relative paths by
        prepending *connect_plugin_path* and home directories (~ prefix)'''
        if not len(value or ''):
            return ''
        value = str(value)
        if value[0] != os.sep and not (
            sys.platform == 'win32' and len(value) >= 2 and value[1] == ':'
        ):
            # A relative path, append plugin path
            value = os.path.join(connect_plugin_path, value)
        elif value.startswith('~/'):
            # A home directory path
            value = os.path.expanduser(value)
        return value

    def _search_filesystem(
        self,
        expression,
        label,
        applicationIdentifier,
        versionExpression=None,
        icon=None,
        launchArguments=None,
        variant='',
        description=None,
        integrations=None,
        standalone_module=None,
        extensions_path=None,
        environment_variables=None,
        connect_plugin_path=None,
        rosetta=False,
    ):
        '''
        Return list of applications found in filesystem matching *expression*.

        *expression* should be a list of regular expressions to match against
        path segments up to the executable. Each path segment traversed will be
        matched against the corresponding expression part. The first expression
        part must not contain any regular expression syntax and must match
        directly to a path existing on disk as it will form the root of the
        search. Example::

            ['C:\\', 'Program Files.*', 'Company', 'Product\d+', 'product.exe']

        *versionExpression* is a regular expression used to find the version of
        *the application. It will be applied against the full matching path of
        *any discovered executable. It must include a named 'version' group
        *which can be used in the label and applicationIdentifier templates.

        For example::

            '(?P<version>[\d]{4})'

        If not specified, then :py:data:`DEFAULT_VERSION_EXPRESSION` will be
        used.

        *label* is the label the application will be given. *label* should be on
        the format "Name of app".

        *applicationIdentifier* should be on the form
        "application_name_{version}" where version is the first match in the
        regexp.

        *launchArguments* may be specified as a list of arguments that should
        used when launching the application.

        *variant* can be used to differentiate between different variants of
        the same application, such as versions. Variant can include '{version}'
        which will be replaced by the matched version.

        *description* can be used to provide a helpful description for the
        user.

        *integrations* is the list of integrations that are required for this
        application to run.

        *standalone_module* is the name of the standalone module that should be
        launched together with the application.

        *extensions_path* is a raw dictionary containing extension paths.

        *environment_variables* is a dictionary of environment variables that
        should be set when launching the application.

        *connect_plugin_path* is the path to the connect plugin folder associated
        with the application/integration.

        *rosetta* dictates if the app needs to be in rosetta mode for Silicon
        chip based Mac.

        '''

        applications = []

        if versionExpression is None:
            versionExpression = DEFAULT_VERSION_EXPRESSION
        else:
            versionExpression = re.compile(versionExpression)

        pieces = expression[:]
        start = pieces.pop(0)

        if self.current_os == 'windows':
            # On Windows C: means current directory so convert roots that look
            # like drive letters to the C:\ format.
            if start and start[-1] == ':':
                start += '\\'

        if not os.path.exists(start):
            raise ValueError(
                'First part "{0}" of expression "{1}" must match exactly to an '
                'existing entry on the filesystem.'.format(start, expression)
            )

        expressions = list(map(re.compile, pieces))
        expressionsCount = len(expressions)

        for location, folders, files in os.walk(
            start, topdown=True, followlinks=True
        ):
            level = location.rstrip(os.path.sep).count(os.path.sep)
            expression = expressions[level]

            if level < (expressionsCount - 1):
                # If not yet at final piece then just prune directories.
                folders[:] = [
                    folder for folder in folders if expression.match(folder)
                ]
            else:
                # Match executable. Note that on OSX executable might equate to
                # a folder (.app).
                for entry in folders + files:
                    match = expression.match(entry)
                    if match:
                        # Extract version from full matching path.
                        path = os.path.join(start, location, entry)

                        versionMatch = versionExpression.search(path)
                        loose_version = LooseVersion('0.0.0')

                        if versionMatch:
                            version = versionMatch.group('version')

                            try:
                                loose_version = LooseVersion(version)
                            except AttributeError:
                                self.logger.warning(
                                    'Could not parse version'
                                    ' {0} from {1}'.format(version, path)
                                )
                        elif sys.platform == 'darwin' and path.endswith(
                            '.app'
                        ):
                            # Extract version from Info.plist within .app
                            # bundle.
                            plist_path = os.path.join(
                                path, 'Contents', 'Info.plist'
                            )
                            if os.path.isfile(plist_path):
                                with open(plist_path, 'rb') as f:
                                    infoPlist = plistlib.load(f)
                                    version = infoPlist.get(
                                        'CFBundleShortVersionString'
                                    )
                                    if version:
                                        loose_version = LooseVersion(version)

                        variant_str = variant.format(
                            version=str(loose_version)
                        )

                        if integrations:
                            variant_str = "{} [{}]".format(
                                variant_str,
                                ':'.join(list(integrations.keys())),
                            )

                        application = {
                            'identifier': applicationIdentifier.format(
                                variant=str(variant_str)
                            ),
                            'path': path,
                            'launchArguments': launchArguments,
                            'version': loose_version,
                            'label': label.format(version=str(loose_version)),
                            'icon': self._get_icon_url(icon),
                            'variant': variant_str,
                            'description': description,
                            'integrations': integrations or {},
                            'rosetta': rosetta,
                        }
                        if standalone_module:
                            application[
                                'standalone_module'
                            ] = standalone_module
                        application['environment_variables'] = {}
                        if extensions_path:
                            # Convert to list and expand paths
                            if isinstance(extensions_path, list):
                                application['environment_variables'][
                                    'FTRACK_FRAMEWORK_EXTENSIONS_PATH'
                                ] = os.pathsep.join(
                                    [
                                        self._conditional_expand_extension_path(
                                            extension_path, connect_plugin_path
                                        )
                                        for extension_path in extensions_path
                                    ]
                                )
                            else:
                                application['environment_variables'][
                                    'FTRACK_FRAMEWORK_EXTENSIONS_PATH'
                                ] = self._conditional_expand_extension_path(
                                    extensions_path, connect_plugin_path
                                )

                        if environment_variables:
                            # Parse environment variables
                            # TODO: support platform specific env vars
                            for name, value in list(
                                environment_variables.items()
                            ):
                                if name.upper() in [
                                    'FTRACK_CONNECT_EXTENSIONS_PATH',
                                    'FTRACK_FRAMEWORK_EXTENSIONS_PATH',
                                ]:
                                    # Ignore these - should be handled in config
                                    self.logger.debug(
                                        f'Ignoring environment variable {name}={value} in launch config -'
                                        f' should be configured in extensions section!'
                                    )
                                    continue
                                if isinstance(value, list):
                                    # Merge on path sep
                                    application['environment_variables'][
                                        name
                                    ] = os.pathsep.join(value)
                                else:
                                    application['environment_variables'][
                                        name
                                    ] = str(value)

                        applications.append(application)

                # Don't descend any further as out of patterns to match.
                del folders[:]

        results = sorted(applications, key=itemgetter('version'), reverse=True)
        self.logger.debug('Discovered applications: {}'.format(results))
        return results


class ApplicationLauncher(object):
    '''Launch applications described by an application store.

    Launched applications are started detached so exiting current process will
    not close launched applications.

    '''

    @property
    def current_os(self):
        return platform.system().lower()

    @property
    def location(self):
        '''Return current location.'''
        return self._session.pick_location()

    @property
    def session(self):
        '''Return current session.'''
        return self._session

    def __init__(self, applicationStore):
        '''Instantiate launcher with *applicationStore* of applications.

        *applicationStore* should be an instance of :class:`ApplicationStore`
        holding information about applications that can be launched.

        '''
        super(ApplicationLauncher, self).__init__()
        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )
        self.applicationStore = applicationStore
        self._session = applicationStore.session

    def discover_integrations(self, application, context):
        context = context or {}
        results = self.session.event_hub.publish(
            ftrack_api.event.base.Event(
                topic='ftrack.connect.application.discover',
                data=dict(
                    application=application,
                    context=context,
                    platform=self.current_os,
                ),
            ),
            synchronous=True,
        )

        requested_integrations = application['integrations']

        discovered_integrations = [
            result.get('integration', {})
            for result in results
            if not result.get('integration', {}).get('disable') is True
        ]

        discovered_integrations_names = set(
            [
                discovered_integration['name']
                for discovered_integration in discovered_integrations
            ]
        )

        found_integrations = discovered_integrations
        lost_integrations = []

        for (
            requested_integration_name,
            requested_integration_items,
        ) in requested_integrations.items():
            # Check if all the requested integration are present in the one available.
            dependency_resolved = not bool(
                set(requested_integration_items).difference(
                    discovered_integrations_names
                )
            )
            if not dependency_resolved:
                lost_integrations.append(requested_integration_name)

        return found_integrations, lost_integrations

    def launch(self, applicationIdentifier, context=None):
        '''Launch application matching *applicationIdentifier*.

        *context* should provide information that can guide how to launch the
        application.

        Return a dictionary of information containing::

            success - A boolean value indicating whether application launched
                      successfully or not.
            message - Any additional information (such as a failure message).

        '''
        # Look up application.
        applicationIdentifierPattern = applicationIdentifier

        application = self.applicationStore.get_application(
            applicationIdentifierPattern
        )

        if application is None:
            return {
                'success': False,
                'message': (
                    '{0} application not found.'.format(applicationIdentifier)
                ),
            }

        # Construct command and environment.
        command = self._get_application_launch_command(application, context)
        environment = self._get_application_environment(application, context)

        # Environment must contain only strings.
        self._conform_environment(environment)

        success = True
        message = '{0}{1} application started.'.format(
            application['label'],
            ' ' + application['variant'] if application.get('variant') else '',
        )

        try:
            options = dict(env=environment, close_fds=True)

            # Ensure that current working directory is set to the root of the
            # application being launched to avoid issues with applications
            # locating shared libraries etc.
            applicationRootPath = os.path.dirname(application['path'])
            options['cwd'] = applicationRootPath

            # Ensure subprocess is detached so closing connect will not also
            # close launched applications.
            if self.current_os == 'windows':
                options['creationflags'] = subprocess.CREATE_NEW_CONSOLE
            else:
                options['preexec_fn'] = os.setsid

            launchData = dict(
                command=command,
                options=options,
                application=application,
                context=context,
                integration={
                    'name': None,
                    'version': None,
                    'env': application.get('environment_variables', {}),
                    'launch_arguments': [],
                },
                platform=self.current_os,
            )

            results = self.session.event_hub.publish(
                ftrack_api.event.base.Event(
                    topic='ftrack.connect.application.launch', data=launchData
                ),
                synchronous=True,
            )

            # recompose launch_arguments coming from integrations
            flatten = lambda t: [item for sublist in t for item in sublist]
            launch_arguments = flatten(
                [
                    r['integration']['launch_arguments']
                    for r in results
                    if (
                        not r is None
                        and 'integration' in r
                        and 'launch_arguments' in r['integration']
                    )
                ]
            )

            launchData['command'].extend(launch_arguments)

            self._notify_integration_use(results, application)

            if context.get('integrations'):
                environment = self._get_integrations_environments(
                    results, context, environment
                )
            else:
                self.logger.info(
                    'No integrations provided for {}:{}'.format(
                        applicationIdentifier, context.get('variant')
                    )
                )

            # Reset variables passed through the hook since they might
            # have been replaced by a handler.
            command = launchData['command']
            options = launchData['options']
            application = launchData['application']
            options['env'] = environment

            enable_app_bundle_launch = (
                True  # Allow .app to be launched directly on Mac
            )
            launch_with_terminal = (
                False  # Launch script with terminal on Mac (console launch)
            )
            command_prefix = None  # Additional commands to prepend

            # Enforce launch architecture
            if 'FTRACK_LAUNCH_ARCH' in environment:
                if self.current_os != 'darwin':
                    self.logger.warning(
                        'Specific arch launch only supported on Mac OS'
                    )
                else:
                    command_prefix = [
                        'arch',
                        '-{}'.format(environment['FTRACK_LAUNCH_ARCH']),
                    ]

                    # This does not work on app bundle, need to be expanded to the executable inside
                    enable_app_bundle_launch = False

            if (os.environ.get('FTRACK_CONNECT_CONSOLE') or '') in [
                '1',
                'true',
            ]:
                if self.current_os != 'darwin':
                    self.logger.warning(
                        'Console launch only supported on Mac OS'
                    )
                else:
                    enable_app_bundle_launch = False
                    launch_with_terminal = True

            if not enable_app_bundle_launch and command[0].lower().endswith(
                '.app'
            ):
                p_script_path = os.path.join(os.environ['TMPDIR'], 'ftrack')
                if not os.path.exists(p_script_path):
                    os.makedirs(p_script_path)
                script_path = tempfile.NamedTemporaryFile(
                    delete=False, dir=p_script_path, suffix='.command'
                ).name

                with open(script_path, "w") as f:
                    f.write('#!/bin/bash\n')

                    for key, value in options['env'].items():
                        f.write('export {}="{}"\n'.format(key, value))

                    app_package = command[0]
                    if app_package.lower().endswith('.app'):
                        # And app bundle, need to launch the executable inside. Discover from
                        # plist.
                        fetch_next_string = False
                        executable_filename = None
                        with open(
                            os.path.join(
                                app_package, 'Contents', 'Info.plist'
                            ),
                            'r',
                        ) as plist:
                            for line in plist.read().split('\n'):
                                if line.find('CFBundleExecutable') > -1:
                                    fetch_next_string = True
                                elif fetch_next_string:
                                    # <string>Nuke13.0</string>
                                    executable_filename = line[
                                        line.find('>') + 1 : line.rfind('<')
                                    ]
                                    break
                        if executable_filename:
                            command[0] = os.path.join(
                                app_package,
                                'Contents',
                                'MacOS',
                                executable_filename,
                            )

                    if command_prefix:
                        command = command_prefix + command

                    commandline = ' '.join('"{}"'.format(c) for c in command)

                    f.write('{}\n'.format(commandline))

                    f.write(
                        'sleep 10\n'
                    )  # Keep console open for 10 seconds, to enable traceback readouts

                os.system('chmod 755 {}'.format(script_path))

                if launch_with_terminal:
                    command = ['open', '-a', 'Terminal', script_path]
                else:
                    command = ['open', script_path]
            else:
                if command_prefix:
                    command = command_prefix + command

            self.logger.debug(
                'Launching {0} with options {1}'.format(command, options)
            )

            process = subprocess.Popen(command, **options)

        except (OSError, TypeError):
            self.logger.exception(
                '{0} application could not be started with command "{1}".'.format(
                    applicationIdentifier, command
                )
            )

            success = False
            message = '{0} application could not be started.'.format(
                application['label']
            )

        else:
            self.logger.debug(
                '{0} application started. (pid={1})'.format(
                    applicationIdentifier, process.pid
                )
            )

            # Check if a standalone framework helper process should be launched

            if 'standalone_module' in application:
                self.logger.info(
                    'Launching standalone framework helper for {0}, module: {1}'.format(
                        applicationIdentifier, application['standalone_module']
                    )
                )

                command = []
                executable_filename = sys.argv[0]
                if not executable_filename.endswith('.py'):
                    command.append(executable_filename)
                else:
                    # Support invocation through Python interpreter
                    command.extend([sys.executable, executable_filename])

                command.extend(
                    [
                        "--run-framework-standalone",
                        application['standalone_module'],
                    ]
                )

                # Append PID to environment for framework to use.
                environment['FTRACK_APPLICATION_PID'] = str(process.pid)

                # Do not show console on Windows
                if self.current_os == 'windows':
                    options["creationflags"] = subprocess.CREATE_NO_WINDOW
                    options["shell"] = True

                    startupinfo = subprocess.STARTUPINFO()
                    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

                    options['startupinfo'] = startupinfo

                try:
                    process = subprocess.Popen(command, **options)
                except (OSError, TypeError):
                    self.logger.exception(
                        'Standalone framework helper process for {0} could not '
                        'be started with command "{1}".'.format(
                            applicationIdentifier, command
                        )
                    )

                    success = False
                    message = (
                        'Standalone framework helper process for {0} could '
                        'not be started.'.format(application['label'])
                    )

                else:
                    self.logger.debug(
                        'Standalone framework helper process for {0} started. '
                        '(pid={1})'.format(applicationIdentifier, process.pid)
                    )

        return {'success': success, 'message': message}

    def _notify_integration_use(self, results, application):
        metadata = {'launched_integrations': []}
        for result in results:
            if result is None:
                continue

            integration = result.get('integration')
            integration_data = {
                'application': "{}_{}".format(
                    application['label'].lower(), str(application['version'])
                ),
                'name': integration['name'].lower(),
                'version': str(integration.get('version', 'Unknown')),
                'os': str(str(platform.platform())),
            }
            metadata['launched_integrations'].append(integration_data)

        usage_tracker = get_usage_tracker()
        if usage_tracker:
            usage_tracker.track("LAUNCHED-CONNECT-INTEGRATION", metadata)

    def _get_integrations_environments(self, results, context, environments):
        # parse integration returned from listeners.
        returned_integrations_names = set(
            [
                result.get('integration', {}).get('name')
                for result in results
                if result
            ]
        )

        self.logger.debug(
            'Discovered integrations {}'.format(returned_integrations_names)
        )
        self.logger.debug(
            'Requested integrations {}'.format(
                list(context.get('integrations', {}).items())
            )
        )

        for integration_group, requested_integration_names in list(
            context.get('integrations', {}).items()
        ):
            difference = set(requested_integration_names).difference(
                returned_integrations_names
            )

            if difference:
                self.logger.warning(
                    'Ignoring group {} as integration/s {} has not been discovered.'.format(
                        integration_group, list(difference)
                    )
                )
                continue

            for requested_integration_name in requested_integration_names:
                result = [
                    result
                    for result in results
                    if result
                    and result['integration']['name']
                    == requested_integration_name
                ][0]

                envs = result['integration'].get('env', {})

                if not envs:
                    self.logger.warning(
                        'No environments exported from integration {}'.format(
                            requested_integration_name
                        )
                    )
                    continue

                self.logger.debug(
                    'Merging environment variables for integration {} for group {}'.format(
                        requested_integration_name, integration_group
                    )
                )

                for key, value in list(envs.items()):
                    action = 'append'  # append by default
                    action_results = key.split('.')

                    if len(action_results) == 2:
                        key, action = action_results

                    if action == 'append':
                        self.logger.debug(
                            'Appending {} with {}'.format(key, value)
                        )
                        append_path(str(value), key, environments)

                    elif action == 'prepend':
                        self.logger.debug(
                            'Prepending {} with {}'.format(key, value)
                        )
                        prepend_path(str(value), key, environments)

                    elif action == 'set':
                        self.logger.debug(
                            'Setting {} to {}'.format(key, value)
                        )
                        environments[key] = str(value)

                    elif action == 'unset':
                        self.logger.debug('Unsetting {}'.format(key))
                        if key in environments:
                            environments.pop(key)

                    elif action == 'pop':
                        self.logger.debug(
                            'removing {} with {}'.format(key, value)
                        )
                        pop_path(str(value), key, environments)

                    else:
                        self.logger.error(
                            'Environment variable action {} not recognised for {}'.format(
                                action, key
                            )
                        )
                        continue

        return environments

    def _get_application_launch_command(self, application, context=None):
        '''Return *application* command based on OS and *context*.

        *application* should be a mapping describing the application, as in the
        :class:`ApplicationStore`.

        *context* should provide additional information about how the
        application should be launched.

        '''
        command = None
        context = context or {}

        if self.current_os in ('windows', 'linux'):
            command = [application['path']]

        elif self.current_os == 'darwin':
            if (os.environ.get('FTRACK_CONNECT_CONSOLE') or '') in [
                '1',
                'true',
            ]:
                command = [application['path']]
            else:
                command = ['open', application['path']]

        else:
            self.logger.warning(
                'Unable to find launch command for {0} on this platform.'.format(
                    application['identifier']
                )
            )

        # Add any extra launch arguments if specified.
        AppLaunchArguments = application.get('launchArguments')
        if AppLaunchArguments:
            command.extend(AppLaunchArguments)

        CtxApplaunchArguments = context.get('launchArguments')
        if CtxApplaunchArguments:
            command.extend(CtxApplaunchArguments)

        return command

    def _get_application_environment(self, application, context=None):
        '''Return mapping of environment for *application* using *context*.

        *application* should be a mapping describing the application, as in the
        :class:`ApplicationStore`.

        *context* should provide additional information about how the
        application should be launched.

        '''
        # Copy all environment variables to new environment and strip the once
        # we know cause problems if copied.
        environment = os.environ.copy()

        environment.pop('PYTHONHOME', None)
        environment.pop('FTRACK_EVENT_PLUGIN_PATH', None)

        # Ensure SSL_CERT_FILE points to the default cert.
        if 'win32' not in sys.platform:
            environment[
                'SSL_CERT_FILE'
            ] = ssl.get_default_verify_paths().cafile

        # Add FTRACK_EVENT_SERVER variable.
        environment = prepend_path(
            self.session.event_hub.get_server_url(),
            'FTRACK_EVENT_SERVER',
            environment,
        )

        # add legacy_environments
        environment['FTRACK_APIKEY'] = self.session.api_key

        laucher_dependencies = os.path.normpath(
            os.path.join(os.path.abspath(os.path.dirname(__file__)), '..')
        )

        environment = prepend_path(
            laucher_dependencies, 'PYTHONPATH', environment
        )

        # Add ftrack connect event to environment.
        if context is not None:
            try:
                applicationContext = base64.b64encode(
                    json.dumps(context).encode("utf-8")
                ).decode('utf-8')
            except (TypeError, ValueError):
                self.logger.exception(
                    'The eventData could not be converted correctly. {0}'.format(
                        context
                    )
                )
            else:
                environment['FTRACK_CONNECT_EVENT'] = applicationContext

        return environment

    def _conform_environment(self, mapping):
        '''Ensure all entries in *mapping* are strings.

        .. note::

            The *mapping* is modified in place.

        '''
        if not isinstance(mapping, MutableMapping):
            return

        for key, value in mapping.copy().items():
            if isinstance(value, Mapping):
                self._conform_environment(value)
            else:
                value = str(value)

            del mapping[key]
            mapping[str(key)] = value


class ApplicationLaunchAction(BaseAction):
    context = []

    def __repr__(self):
        return "<label:{}|id:{}|variant:{}>".format(
            self.label, self.identifier, self.variant
        )

    @property
    def session(self):
        '''Return convenient exposure of the self._session reference.'''
        return self._session

    def __init__(
        self, session, application_store, launcher, priority=sys.maxsize
    ):
        super(ApplicationLaunchAction, self).__init__(session)

        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )

        self.priority = priority
        self.application_store = application_store
        self.launcher = launcher

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
        resolved_entity_type = self.session.get(
            entity_type, entity_id
        ).entity_type

        if resolved_entity_type in self.context:
            return True

        return False

    def _discover(self, event):
        entities, event = self._translate_event(self.session, event)

        if not self.validate_selection(entities):
            return

        items = []
        applications = self.application_store.applications

        applications = sorted(
            applications, key=lambda application: application['label']
        )

        for application in applications:
            application_identifier = application['identifier']
            label = application['label']

            context = event['data'].copy()
            context['source'] = event['source']

            if self.launcher and application.get('integrations'):
                (
                    _,
                    lost_integration_groups,
                ) = self.launcher.discover_integrations(application, context)

                for lost_integration_group in lost_integration_groups:
                    removed_integrations = application['integrations'][
                        lost_integration_group
                    ]
                    self.logger.debug(
                        (
                            'Application integration group {} for {} {} could not be loaded.\n'
                            'Some of the integrations defined could not be found: {}'
                        ).format(
                            lost_integration_group,
                            application['label'],
                            application['variant'],
                            removed_integrations,
                        )
                    )

                if lost_integration_groups:
                    continue

            items.append(
                {
                    'actionIdentifier': self.identifier,
                    'label': label,
                    'icon': application.get('icon', 'default'),
                    'variant': application.get('variant', None),
                    'applicationIdentifier': application_identifier,
                    'integrations': application.get('integrations', {}),
                    'host': platform.node(),
                    'rosetta': application.get('rosetta', None),
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

    def get_debug_information(self):
        '''Get application launcher debug information'''
        result = {'identifier': self.identifier, 'applications': []}
        for application in self.application_store.applications:
            application_information = {
                k: str(v) for k, v in application.items()
            }
            founds = []
            all_discovered, _ = self.launcher.discover_integrations(
                application, None
            )
            for discovered in all_discovered:
                if discovered not in founds:
                    founds.append(discovered)
            application_information['found'] = founds
            result['applications'].append(application_information)
        return result

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
