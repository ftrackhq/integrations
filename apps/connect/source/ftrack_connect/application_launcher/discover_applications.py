import sys
import os
import platform
from collections import defaultdict
import logging
import yaml

from ftrack_utils.extensions.registry import register_yaml_files

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
        loaded_filtered_files = []
        for config_path in config_paths:
            if not os.path.exists(config_path) or not os.path.isdir(
                config_path
            ):
                self.logger.warning(
                    '{} directory cannot be found.'.format(config_path)
                )
                continue

            files = os.listdir(config_path)

            yaml_config_file_paths = [
                os.path.join(config_path, str(config))
                for config in files
                if config.endswith('yaml')
            ]

            for extension in register_yaml_files(yaml_config_file_paths):
                loaded_filtered_files.append(
                    (extension['extension'], extension['path'])
                )
                self.logger.info(
                    'Found launcher config extension: {}'.format(
                        extension['path']
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
            result_dict.setdefault(configuration['identifier'], []).append(
                (configuration, path)
            )

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
                # Does the launcher needs the app on roseta mode?
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

    def register(self):
        for action in self._actions:
            action.register()
