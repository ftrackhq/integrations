# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import importlib
import glob
import os
import pkgutil
import platform
import platformdirs
import re
import socket
import time

from copy import deepcopy
from omegaconf import OmegaConf
from pathlib import Path
from pydantic.utils import deep_update


def register_resolvers():
    # These will be lazily evaluated when the config is accessed
    # TODO: Filling in the runtime args like this is up for discussion as we could also handle it differently.
    def _runtime_startup(key: str):
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
        match key:
            case "time":
                return time.time()
            case _:
                return "None"

    # TODO: Use platformdirs to fill in the platform specific paths
    def _paths(path_type: str, scope: str):
        method_name = f"{scope}_{path_type}_path"
        supported_path_types = [
            _.split("_")[1] for _ in dir(platformdirs) if re.match(r"user_.+_path", _)
        ]
        if path_type not in supported_path_types:
            raise ValueError(
                f"Path type {path_type} cannot be resolved. Supported path types are {supported_path_types}"
            )

        method = getattr(platformdirs, method_name)
        assert method
        return method("ftrack-connect")

    def _glob(key):
        matches = glob.glob(key)
        return matches

    # TODO: maybe we should resolve regex paths into lists using a resolver
    #  this way we can just resolve and see the result within the final yaml config
    def _regex(value, pattern):
        if isinstance(value, str):
            value = [value]

        matches = []
        for v in value:
            if match := re.search(pattern, v):
                matches.append(match[0])

        return matches

    def _lower(key: str):
        return key.lower()

    def _compose(references: list[str], *, _node_, _parent_, _root_):
        my_key = _node_._key()
        # We have to remove our current node to not end up in an infinite recursion.
        # The infinite recursion happens because we're hitting the resolver every time we access a key.
        # We can't work around this by using the cache, as caching is not supported in combination with
        # special argument access (_node_, _parent_, _root_).
        config = OmegaConf.create({})
        for reference in references:
            config = deep_update(config, reference)

        # OmegaConf.resolve(config)
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
        lambda *references, _node_, _parent_, _root_: _compose(
            references, _node_=_node_, _parent_=_parent_, _root_=_root_
        ),
    )


def get_configuration_files_from_namespace(
    namespace: str = "ftrack.library",
) -> list[Path]:
    configuration_files = []
    root_namespace_package = importlib.import_module(namespace)
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
            for _file in os.listdir(module_path):
                if re.match(r".*\.(yml|yaml)$", _file):
                    full_path = module_path / _file
                    configuration_files.append(full_path)

    return configuration_files


def compose_configuration_from_files(filepaths: list[Path]):
    merged_configuration = OmegaConf.create()
    for filepath in filepaths:
        configuration = OmegaConf.load(filepath)
        merged_configuration = OmegaConf.merge(merged_configuration, configuration)
    return merged_configuration


def resolve_configuration_to_dict(configuration, cleanup=True) -> dict:
    resolved_configuration = OmegaConf.to_container(configuration, resolve=True)

    def _recursive_cleanup(root):
        keys_to_delete = []
        for key, value in root.items():
            if key.startswith("+"):
                keys_to_delete.append(key)
                continue
            if isinstance(value, dict):
                _recursive_cleanup(value)
        for key in keys_to_delete:
            del root[key]

    _recursive_cleanup(resolved_configuration)

    return resolved_configuration


def interpolate_configuration_values():
    pass


def inject_builtin_configuration_values():
    # TODO: This might not be needed when using resolvers
    pass


def inject_named_regex_groups():
    pass
