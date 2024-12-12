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
import omegaconf
from omegaconf import OmegaConf
from pathlib import Path


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

    def _compose(key: str, *, _node_, _parent_, _root_):
        my_key = _node_._key()
        # We have to remove our current node to not end up in an infinite recursion.
        # The infinite recursion happens because we're hitting the resolver every time we access a key.
        # We can't work around this by using the cache, as caching is not supported in combination with
        # special argument access (_node_, _parent_, _root_).
        del _parent_[my_key]

        compose_pattern = re.compile(f"\++({my_key})")

        composable_keys = []
        for key, value in _parent_.items():
            if re.match(compose_pattern, key):
                _node_.update(_parent_[key])

        # print(_node_._get_full_key(_node_._key()))

        # resolved_config = OmegaConf.resolve(_parent_)
        # _parent_.create({"foobar": "baz"})
        return _node_

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
        lambda key, *, _node_, _parent_, _root_: _compose(
            key, _node_=_node_, _parent_=_parent_, _root_=_root_
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


# def merge_configuration_files():
#     """
#     Merges configuration files into a single configuration object
#     :return:
#     """
#     pass
#
# def compose_configuration(data: str) -> dict:
#     pass
#
# def interpolate_configuration_values(data: dict):
#     pass


def compose_configuration_from_files(filepaths: list[Path]):
    merged_configuration = OmegaConf.create()
    for filepath in filepaths:
        configuration = OmegaConf.load(filepath)
        merged_configuration = OmegaConf.merge(merged_configuration, configuration)
    return merged_configuration


def cleanup_configuration():
    # TODO: clean up all "composable" keys that start with a +
    pass


def interpolate_configuration_values():
    pass


def inject_builtin_configuration_values():
    # TODO: This might not be needed when using resolvers
    pass


def inject_named_regex_groups():
    pass
