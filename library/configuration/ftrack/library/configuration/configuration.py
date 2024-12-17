# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import importlib
import glob
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

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


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
                reference.get("delete_after_compose")
                and not full_reference_key in reference
            ):
                _root_._delete_after_compose.append(full_reference_key)
                # Delete this key from the final composed config
                del config.delete_after_compose

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


def get_configuration_files_from_namespace(
    namespace: str = "ftrack.library",
) -> set[Path]:
    """
    Get all configuration files from a given namespace.
    We will not search recursively, only the top level of the given paths will be searched.

    :param namespace: The namespace within the available packages to search for configuration files.
    :return: A list of paths to the configuration files.
    """

    configuration_files = []
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
            configuration_files.extend(_get_files_from_path(module_path))

    return set(configuration_files)


def get_configuration_files_from_entrypoint(
    name: str = "connect.configuration",
) -> set[Path]:
    """
    Get all configuration files from a given entrypoint.
    We will not search recursively, only the top level of the given paths will be searched.

    :param name: The name of the entry point to look for configuration files.
    :return: A list of paths to the configuration files.
    """
    configuration_files = []
    for entrypoint in entry_points()[name]:
        # load the configuration entry point so we execute and initialise any custom resolvers
        configuration_package = entrypoint.load()

        module_path = Path(configuration_package.__file__).parent
        configuration_files.extend(_get_files_from_path(module_path))

    return set(configuration_files)


def get_configuration_files_from_paths(
    paths: set[Path] = "connect.configuration",
) -> set[Path]:
    """
    Get all configuration files from a given set of paths.
    We will not search recursively, only the top level of the given paths will be searched.

    :param paths: A set of parent paths to search for configuration files.
    :return: A list of paths to the configuration files.
    """
    configuration_files = []
    for path in paths:
        configuration_files.extend(_get_files_from_path(path))
    return set(configuration_files)


def compose_configuration_from_files(
    filepaths: Union[list[Path], set[Path]]
) -> DictConfig:
    """
    Given a list of configuration file paths, load and merge them into a single configuration object.

    :param filepaths: A list of Path objects pointing to the configuration files.
    :return: A DictConfig object containing the merged configuration.
    """
    merged_configuration = OmegaConf.create()
    for filepath in filepaths:
        configuration = OmegaConf.load(filepath)
        merged_configuration = OmegaConf.merge(merged_configuration, configuration)
    return merged_configuration


# TODO: we should MAYBE not only take DictConfig, but also Listconfig into account
def resolve_configuration(configuration: DictConfig) -> DictConfig:
    """
    Resolves all interpolation keys and executes all resolvers in the given configuration object.
    We will also delete all keys that are marked for deletion after composition.

    :param configuration: The configuration object to resolve.
    :return: The resolved configuration object.
    """
    resolved_configuration = deepcopy(configuration)
    resolved_configuration = OmegaConf.merge(
        resolved_configuration, DictConfig({"_delete_after_compose": ListConfig([])})
    )
    OmegaConf.resolve(resolved_configuration)

    for value in resolved_configuration._delete_after_compose:
        reference = OmegaConf.select(resolved_configuration, value)
        if reference:
            parent = reference._parent
            del parent[reference._key()]

    del resolved_configuration._delete_after_compose

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

    def _recursive_cleanup(root):
        keys_to_delete = []
        for key, value in root.items():
            if key.startswith(pattern):
                keys_to_delete.append(key)
                continue
            if isinstance(value, dict):
                _recursive_cleanup(value)
        for key in keys_to_delete:
            del root[key]

    cleaned_configuration = deepcopy(configuration)
    _recursive_cleanup(cleaned_configuration)
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
