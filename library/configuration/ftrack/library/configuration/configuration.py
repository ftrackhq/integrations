# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

"""
This module provides functionality to load, merge, resolve and save configuration files.
The utilities in this module are designed to work nicely together.
They are supposed to be run in sequence. For example:

>>> register_resolvers()
>>> config_files = get_configurations_from_entrypoint("connect.configuration")
>>> more_config_files = get_configurations_from_namespace("ftrack.library")
>>> all_config_files = config_files.union(more_config_files)

>>> composed_configuration = compose_configuration_from_configurations(config_files)
>>> resolved_configuration = resolve_configuration(composed_configuration)
>>> save_configuration_to_yaml(resolved_configuration, Path("resolved.yaml"))
"""

import glob
import importlib
import itertools
import logging
import os
import pkgutil
import platform

import platformdirs
import re
import socket
import time

from copy import deepcopy
from importlib.metadata import entry_points
from pathlib import Path
from types import ModuleType
from typing import (
    Any,
    Union,
)

from omegaconf import OmegaConf, DictConfig, ListConfig
from pydantic.v1.utils import deep_update

# log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


METADATA_ROOT_KEY = "_metadata"
METADATA_SOURCES_KEY = "sources"
METADATA_DELETE_KEY = "delete-after-compose"
METADATA_CONFLICTS_KEY = "conflicts"


class Configuration:
    def __init__(
        self,
        package_name: str = "",
        file_path: Path = "",
        configuration: DictConfig = OmegaConf.create({}),
    ):
        self.package_name = package_name
        self.file_path = file_path
        self.configuration = configuration

    # TODO: This should probably just be the string representation
    @property
    def identifier(self):
        if self.package_name and self.file_path:
            return f"{self.package_name}:{self.file_path.name}"
        elif self.file_path:
            return self.file_path
        else:
            return None

    def __hash__(self):
        return hash(self.file_path)


def register_resolvers() -> None:
    """
    Defines and registers all custom resolvers that can be used in the configuration files.
    We namespace our internal resolvers with ft.* to avoid conflicts with other resolvers.

    :return: None
    """

    # TODO: Filling in the runtime args like this is up for discussion as we could also handle it differently.
    # These will be lazily evaluated when the config is accessed
    def _runtime_cached(value: str):
        # All of these will be cached and only evaluated once.
        match value:
            case "architecture":
                return platform.architecture()[0]
            case "platform":
                return platform.system()
            case "username":
                return os.getlogin()
            case "hostname":
                return socket.gethostname()
            case "python_version":
                return platform.python_version()
            case "time":
                return time.time()
            case "file":
                return time.time()
            case _:
                return "None"

    def _runtime_live(value: str):
        # All of these will be evaluated every time the config value is accessed.
        match value:
            case "time":
                return time.time()
            case _:
                return "None"

    def _paths(path_type: str, scope: str) -> str:
        path_getter_method_name = f"{scope}_{path_type}_path"
        supported_path_types = [
            _.split("_")[1] for _ in dir(platformdirs) if re.match(r"user_.+_path", _)
        ]
        if path_type not in supported_path_types:
            raise ValueError(
                f"Path type {path_type} cannot be resolved. Supported path types are {supported_path_types}"
            )

        path_getter_method = getattr(platformdirs, path_getter_method_name)
        assert path_getter_method
        return path_getter_method("ftrack-connect").as_posix()

    def _glob(value: str) -> ListConfig:
        """
        Match all paths that match the given glob pattern.

        :param value:
        :return: A ListConfig object containing all the matched paths.
        """
        matches = glob.glob(value)
        return OmegaConf.create(matches)

    def _regex(value, pattern) -> ListConfig:
        """
        Match all values that match the given regex pattern.

        :param value: The value to match against.
        :param pattern: The regex pattern for matching.
        :return: A ListConfig object containing all the matched values.
        """
        if not isinstance(value, list):
            value = [value]

        matches = []
        for v in value:
            if match := re.search(pattern, str(v)):
                matches.append(match[0])

        return OmegaConf.create(matches)

    def _lower(value: str) -> str:
        """
        Lowercases the given value.
        :param key:
        :return:
        """
        return value.lower()

    def _compose(references: list[Any], *, _node_, _root_) -> DictConfig:
        """
        Composes the given references into a single configuration object.

        Example:
        launch: "${ft.compose: ${configuration.maya-default.launch}, ${.my_override}, ${.my_other_override}}"
        my_override::
          delete_after_compose: True
          discovery-hook: "my_override"
        my_other_override:
          windows: "C:\*"

        The above example will compose configuration.maya-default.launch, my_override and my_other_override.
        The composition is done in order and sparsely, meaning we'll match and add/replace the lowest possible
        node in the hierarchy.
        Additionally, we will delete the my_override key after composing it due to it having the delete_after_compose
        flag set to True.

        :param references: A List of references.
        :param _node_: The implicitly provided current node.
        :param _root_: The implicitly provided root node of the configuration.
        :return: A DictConfig object containing the composed configuration.
        """
        config = OmegaConf.create({})
        for reference in references:
            config = deep_update(config, reference)
            full_reference_key = reference._parent._get_full_key(reference._key())
            if (
                reference.get(METADATA_ROOT_KEY, {}).get(METADATA_DELETE_KEY, False)
                and full_reference_key
                not in _root_[METADATA_ROOT_KEY][METADATA_DELETE_KEY]
            ):
                _root_[METADATA_ROOT_KEY][METADATA_DELETE_KEY][
                    full_reference_key
                ] = reference
                # Delete this key from the final composed config
                del config[METADATA_ROOT_KEY]

        return config

    OmegaConf.register_new_resolver(
        "ft.runtime.cached", lambda key: _runtime_cached(key), use_cache=True
    )
    OmegaConf.register_new_resolver("ft.runtime.live", lambda key: _runtime_live(key))
    OmegaConf.register_new_resolver(
        "ft.paths",
        lambda path_type, scope="user": _paths(path_type, scope),
        use_cache=True,
    )
    OmegaConf.register_new_resolver("ft.lower", lambda key: _lower(key))
    OmegaConf.register_new_resolver(
        "ft.regex", lambda value, pattern: _regex(value, pattern)
    )
    OmegaConf.register_new_resolver("ft.glob", lambda key: _glob(key))
    OmegaConf.register_new_resolver(
        "ft.compose",
        lambda *references, _node_, _root_: _compose(
            references, _node_=_node_, _root_=_root_
        ),
    )


def _get_files_from_path(path: Path, pattern=r".*\.(yml|yaml)$") -> list[Path]:
    """
    Get all files from a given path that match the given pattern.
    We will only return top level files, no recursion is done.

    :param path: The parent path to search for files.
    :param pattern: The regex pattern to apply to the filenames.
    :return: A list of paths to the files that match the pattern.
    """
    files = []
    for _file in os.listdir(path):
        if re.match(pattern, _file):
            full_path = path / _file
            files.append(full_path)
    return files


def get_configurations_from_namespace(
    namespace: str = "ftrack.library",
) -> set[Configuration]:
    """
    Get all configuration files from a given namespace.
    We will not search recursively, only the top level of the given paths will be searched.

    :param namespace: The namespace within the available packages to search for configuration files.
    :return: A list of paths to the configuration files.
    """

    configuration_sources = []
    root_namespace_package: ModuleType = importlib.import_module(namespace)
    packages = pkgutil.walk_packages(
        root_namespace_package.__path__, prefix=root_namespace_package.__name__ + "."
    )

    for package in packages:
        module_spec = package.module_finder.find_spec(package.name)
        # check if this is a package (non-packages will have a submodule_search_locations attribute of None)
        if (
            module_spec.submodule_search_locations
            and module_spec.name.split(".")[-1] == "configuration"
        ):
            module_path = Path(module_spec.origin).parent
            for _file in _get_files_from_path(module_path):
                configuration_sources.append(
                    Configuration(package_name=package.name, file_path=_file)
                )

    return set(configuration_sources)


def get_configurations_from_entrypoint(
    name: str = "connect.configuration",
) -> set[Configuration]:
    """
    Get all configuration files from a given entrypoint.
    We will not search recursively, only the top level of the given paths will be searched.

    :param name: The name of the entry point to look for configuration files.
    :return: A list of paths to the configuration files.
    """
    configuration_sources = []
    for entrypoint in entry_points()[name]:
        # load the configuration entry point so we execute and initialise any custom resolvers
        configuration_package = entrypoint.load()

        module_path = Path(configuration_package.__file__).parent
        for _file in _get_files_from_path(module_path):
            configuration_sources.append(
                Configuration(
                    package_name=configuration_package.__name__, file_path=_file
                )
            )

    return set(configuration_sources)


def get_configurations_from_paths(
    paths: list[Path] = "connect.configuration",
) -> set[Configuration]:
    """
    Get all configuration files from a given set of paths.
    We will not search recursively, only the top level of the given paths will be searched.

    :param paths: A set of parent paths to search for configuration files.
    :return: A list of paths to the configuration files.
    """
    configuration_sources = []
    for path in paths:
        for _file in _get_files_from_path(path):
            configuration_sources.append(
                Configuration(package_name="", file_path=_file)
            )
    return set(configuration_sources)


def compose_configuration_from_configurations(
    configurations: list[Configuration],
) -> DictConfig:
    """
    Given a list of configuration file paths, load and merge them into a single configuration object.

    :param filepaths: A list of Path objects pointing to the configuration files.
    :return: A DictConfig object containing the merged configuration.
    """

    def _check_for_conflicts(lhs, rhs, root_key):
        conflicting_keys = []
        for key in lhs.get(root_key, []):
            if key in rhs.get(root_key, []):
                conflicting_keys.append(f"{root_key}.{key}")
        return conflicting_keys

    merged_configuration = OmegaConf.create(
        {
            METADATA_ROOT_KEY: {
                METADATA_SOURCES_KEY: ListConfig([]),
                METADATA_DELETE_KEY: DictConfig({}),
                METADATA_CONFLICTS_KEY: DictConfig({}),
            }
        }
    )

    # add the actual configuration
    for configuration in configurations:
        configuration.configuration = OmegaConf.load(configuration.file_path)

    # remove any empty configuration from the list
    non_empty_configurations = [_ for _ in configurations if _.configuration]

    # create all possible combinations of two configurations to compare them against
    # each other for conflicts
    combinations_for_conflict_checking = list(
        itertools.combinations(non_empty_configurations, 2)
    )

    # we will check for conflicts and report on them, but not attempt any automatic conflict resolution
    from collections import defaultdict

    conflicts = defaultdict(list)
    for lhs, rhs in combinations_for_conflict_checking:
        if configuration_conflict_keys := _check_for_conflicts(
            lhs.configuration, rhs.configuration, "configuration"
        ):
            logging.error(
                "Configurations with overlapping keys have been found. "
                "Please make sure to explicitly set a resolution order.:"
            )
            logging.error(lhs.identifier)
            logging.error(rhs.identifier)
            logging.error(f"{configuration_conflict_keys}")
            for configuration_conflict_key in configuration_conflict_keys:
                conflicts[configuration_conflict_key].extend(
                    [lhs.identifier, rhs.identifier]
                )
    # Make sure that the root level entries in conflicts are unique by a transient conversion to a set.
    conflicts = {key: list(set(value)) for key, value in conflicts.items()}
    merged_configuration[METADATA_ROOT_KEY][METADATA_CONFLICTS_KEY] = dict(conflicts)

    for configuration in sorted(
        non_empty_configurations, key=lambda x: f"{x.package_name}:{x.file_path}"
    ):
        if configuration.configuration.get(METADATA_ROOT_KEY):
            del configuration.configuration[METADATA_ROOT_KEY]
        merged_configuration[METADATA_ROOT_KEY][METADATA_SOURCES_KEY].append(
            configuration.identifier
        )
        merged_configuration = OmegaConf.merge(
            merged_configuration, configuration.configuration
        )
    return merged_configuration


# TODO: we should MAYBE not only take DictConfig, but also Listconfig into account
def resolve_configuration(configuration: DictConfig) -> DictConfig:
    """
    Resolves all interpolation keys and executes all resolvers in the given configuration object.
    We will also delete all keys that are marked for deletion after composition.
    Deleted keys are "moved" into the global _metadata key for later reference.

    :param configuration: The configuration object to resolve.
    :return: The resolved configuration object.
    """
    resolved_configuration = deepcopy(configuration)
    # resolved_configuration = OmegaConf.merge(
    #     resolved_configuration, DictConfig({"_delete_after_compose": ListConfig([])})
    # )
    OmegaConf.resolve(resolved_configuration)

    for key in resolved_configuration[METADATA_ROOT_KEY][METADATA_DELETE_KEY]:
        reference = OmegaConf.select(resolved_configuration, key)
        if reference:
            parent = reference._parent
            del parent[reference._key()]

    # del resolved_configuration._delete_after_compose

    return resolved_configuration


def remove_keys_from_configuration(
    configuration: DictConfig, pattern: str = "+"
) -> DictConfig:
    """
    Remove all keys from the configuration that match the given pattern.

    :param configuration: The configuration object to remove keys from.
    :param pattern: The pattern to match the keys against.
    :return: A cleaned up configuration object.
    """

    def _recursive_remove(root):
        keys_to_delete = []
        for key, value in root.items():
            if key.startswith(pattern):
                keys_to_delete.append(key)
                continue
            if isinstance(value, dict):
                _recursive_remove(value)
        for key in keys_to_delete:
            del root[key]

    cleaned_configuration = deepcopy(configuration)
    _recursive_remove(cleaned_configuration)
    return cleaned_configuration


def convert_configuration_to_dict(configuration: DictConfig) -> dict:
    """
    Resolves the given configuration object into a dictionary.
    This will not automatically resolve the configuration.

    :param configuration: The configuration object to resolve.
    :param resolve: Whether to resolve the configuration or not.
    :return: The resolved and possibly cleaned up configuration as a dictionary.
    """
    resolved_configuration = OmegaConf.to_container(configuration, resolve=False)
    return resolved_configuration


def save_configuration_to_yaml(configuration: DictConfig, path: Path) -> None:
    """
    Safely write the configuration to a yaml file.
    This will not automatically resolve the configuration.

    :param configuration: The configuration object to write.
    :param path: The path to write the configuration to.
    :return: None
    """
    OmegaConf.save(configuration, path)
