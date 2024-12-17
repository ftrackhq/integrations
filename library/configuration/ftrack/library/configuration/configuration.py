# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import importlib
import glob
import os
import logging
import pkgutil
import platform
import platformdirs
import re
import socket
import time

from copy import deepcopy
from pathlib import Path
from types import ModuleType
from typing import Any, Union
from importlib.metadata import entry_points, EntryPoint

from omegaconf import OmegaConf, DictConfig, ListConfig
from pydantic.v1.utils import deep_update

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def register_resolvers():
    """
    Defines and registers all custom resolvers that can be used in the configuration files.

    :return:
    """

    # TODO: Filling in the runtime args like this is up for discussion as we could also handle it differently.
    # These will be lazily evaluated when the config is accessed
    def _runtime_startup(key: str):
        # All of these will be cached and only evaluated once.
        match key:
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

    def _runtime_live(key: str):
        # All of these will be evaluated every time the config value is accessed.
        match key:
            case "time":
                return time.time()
            case _:
                return "None"

    def _paths(path_type: str, scope: str) -> Path:
        path_getter_method_name = f"{scope}_{path_type}_path"
        supported_path_types = [
            _.split("_")[1] for _ in dir(platformdirs) if re.match(r"user_.+_path", _)
        ]
        if path_type not in supported_path_types:
            raise ValueError(
                f"Path type {path_type} cannot be resolved. Supported path types are {supported_path_types}"
            )

        path_getter_method: callable = getattr(platformdirs, path_getter_method_name)
        assert path_getter_method
        return Path(path_getter_method("ftrack-connect"))

    def _glob(key: str) -> ListConfig:
        """
        Match all paths that match the given glob pattern.
        :param key:
        :return:
        """
        matches = glob.glob(key)
        return OmegaConf.create(matches)

    # TODO: maybe we should resolve regex paths into lists using a resolver
    #  this way we can just resolve and see the result within the final yaml config
    def _regex(value, pattern) -> ListConfig:
        if not isinstance(value, list):
            value = [value]

        matches = []
        for v in value:
            if match := re.search(pattern, str(v)):
                matches.append(match[0])

        return OmegaConf.create(matches)

    def _lower(key: str) -> str:
        return key.lower()

    def _compose(references: list[Any], *, _node_) -> DictConfig:
        # We have to remove our current node to not end up in an infinite recursion.
        # The infinite recursion happens because we're hitting the resolver every time we access a key.
        # We can't work around this by using the cache, as caching is not supported in combination with
        # special argument access (_node_, _parent_, _root_).
        config = OmegaConf.create({})
        for reference in references:
            config = deep_update(config, reference)

        return config

    OmegaConf.register_new_resolver(
        "runtime.startup", lambda key: _runtime_startup(key), use_cache=True
    )
    OmegaConf.register_new_resolver("runtime.live", lambda key: _runtime_live(key))
    OmegaConf.register_new_resolver(
        "paths",
        lambda path_type, scope="user": _paths(path_type, scope),
        use_cache=True,
    )
    OmegaConf.register_new_resolver("lower", lambda key: _lower(key))
    OmegaConf.register_new_resolver(
        "regex", lambda value, pattern: _regex(value, pattern)
    )
    OmegaConf.register_new_resolver("glob", lambda key: _glob(key))
    OmegaConf.register_new_resolver(
        "compose",
        lambda *references, _node_: _compose(references, _node_=_node_),
    )


def _get_files_from_path(path: Path, pattern=r".*\.(yml|yaml)$") -> list[Path]:
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
    resolved_configuration = deepcopy(configuration)
    OmegaConf.resolve(resolved_configuration)
    return resolved_configuration


def remove_keys_from_configuration(
    configuration: DictConfig, pattern: str = "+"
) -> DictConfig:
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


def convert_configuration_to_dict(
    configuration: DictConfig, resolve: bool = True
) -> dict:
    """
    Resolves the given configuration object into a dictionary.
    This will also flatten/resolve all individual keys to their final values.

    :param configuration: The configuration object to resolve.
    :param resolve: Whether to resolve the configuration or not.
    :return: The resolved and possibly cleaned up configuration as a dictionary.
    """

    resolved_configuration = OmegaConf.to_container(configuration, resolve=resolve)
    return resolved_configuration
