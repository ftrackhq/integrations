# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import sys
import os
import platform
from collections import defaultdict
import logging

from ftrack_connect.utils.environment import (
    get_connect_extensions_path_from_environment,
)
from ftrack_framework_core import registry

from ftrack_connect.application_launcher import (
    ApplicationStore,
    ApplicationLaunchAction,
    ApplicationLauncher,
)


class DiscoverApplications(object):
    @property
    def current_os(self):
        return platform.system().lower()

    def __init__(self, session, applications_config_paths):
        super(DiscoverApplications, self).__init__()
        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )

        # If a single path is passed by mistake, handle it here.
        if isinstance(applications_config_paths, str):
            applications_config_paths = [applications_config_paths]

        self._actions = []

        self._session = session
        configurations = self._parse_configurations(applications_config_paths)
        self._build_launchers(configurations)

    def _parse_configurations(self, config_paths):
        '''Use the extensions library to load and merge launch configurations'''
        loaded_filtered_files = []
        connect_extensions_path = (
            get_connect_extensions_path_from_environment()
        )
        for config_path in config_paths:
            if not os.path.exists(config_path) or not os.path.isdir(
                config_path
            ):
                self.logger.warning(
                    '{} directory cannot be found.'.format(config_path)
                )
                continue

            connect_extensions_path.append(config_path)

        # Load and merge all launch configs from the extensions path
        registry_instance = registry.Registry()
        registry_instance.scan_extensions(
            paths=connect_extensions_path, extension_types=['launch_config']
        )

        for launcher_extension in registry_instance.launch_configs or []:
            loaded_filtered_files.append(
                (launcher_extension['extension'], launcher_extension['path'])
            )
            self.logger.info(
                'Loaded launcher config extension: {}'.format(
                    launcher_extension['extension']
                )
            )

        self.logger.debug(
            'Launcher configs found: {}'.format(len(loaded_filtered_files))
        )

        return loaded_filtered_files

    def _group_configurations(self, configurations):
        '''group configuration based on identifier'''
        result_dict = defaultdict(list)

        for configuration, path in configurations:
            try:
                result_dict.setdefault(configuration['identifier'], []).append(
                    (configuration, path)
                )
            except Exception as e:
                self.logger.warning(
                    f"The following launcher configuration from path {path} can't be loaded, the configuration is probably incomplete. Ignoring it. \n Error: {e} \n Configuration:{configuration} "
                )
                continue

        return result_dict

    def _build_launchers(self, configurations):
        grouped_configurations = self._group_configurations(configurations)
        for (
            identifier,
            identified_configuration,
        ) in grouped_configurations.items():
            self.logger.debug(
                'building config store for {}({})'.format(
                    identifier, len(identified_configuration)
                )
            )
            store = ApplicationStore(self._session)

            for config, config_path in identified_configuration:
                # extract data from app config
                search_path = config['search_path'].get(self.current_os)
                if not search_path:
                    self.logger.info(
                        'No entry found for os: {} in config {}'.format(
                            self.current_os, config['label']
                        )
                    )
                    continue

                launch_arguments = search_path.get('launch_arguments')
                prefix = search_path['prefix']
                expression = search_path['expression']
                version_expression = search_path.get('version_expression')
                # Does the launcher needs the app on rosetta mode?
                rosetta = search_path.get('rosetta')
                applications = store._search_filesystem(
                    versionExpression=version_expression,
                    expression=prefix + expression,
                    label=config['label'],
                    applicationIdentifier=config['applicationIdentifier'],
                    icon=config['icon'],
                    variant=config['variant'],
                    launchArguments=launch_arguments,
                    integrations=config.get('integrations'),
                    standalone_module=config.get('standalone_module'),
                    extensions_path=config.get('extensions_path'),
                    environment_variables=config.get('environment_variables'),
                    connect_plugin_path=os.path.realpath(
                        os.path.join(os.path.dirname(config_path), '..')
                    ),
                    rosetta=rosetta,
                )
                store.applications.extend(applications)

            launcher = ApplicationLauncher(store)
            NewAction = type(
                'ApplicationLauncherAction-{}'.format(config['label']),
                (ApplicationLaunchAction,),
                {
                    'label': config['label'],
                    'identifier': identifier,
                    'context': config['context'],
                },
            )
            priority = config.get('priority', sys.maxsize)
            action = NewAction(
                self._session, store, launcher, priority=priority
            )

            self.logger.debug(
                'Creating App launcher {} with priority {}'.format(
                    action, priority
                )
            )

            self._actions.append(action)

    def get_debug_information(self):
        '''Return all launcher actions as debug information'''
        result = {
            'name': 'Application Launcher',
            'identifier': 'application.launch',
            'actions': [],
        }
        for action in self._actions:
            result['actions'].append(action.get_debug_information())
        return result

    def register(self):
        for action in self._actions:
            action.register()

        self.logger.debug('Registered {} action(s)'.format(len(self._actions)))
