# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import importlib
import os
import pkgutil
import platform
import re
import socket
import time
import omegaconf
from omegaconf import OmegaConf
from pathlib import Path


def register_resolvers():
    # These will be lazily evaluated when the config is accessed
    # TODO: This is up for discussion as we could also handle it differently.
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

    def _paths(path_type: str, platform: str):
        if path_type == "config":
            match platform:
                case "windows":
                    return Path("C:/ProgramData/ftrack/library")
                case "linux":
                    return Path("/opt/ftrack/library")
                case "darwin":
                    return Path("/Applications/ftrack/library")
                case _:
                    return ""

    def _lower(key: str):
        return key.lower()

    OmegaConf.register_new_resolver("runtime.startup", lambda key: _runtime_startup(key), use_cache=True)
    OmegaConf.register_new_resolver("runtime.live", lambda key: _runtime_live(key))
    OmegaConf.register_new_resolver("paths", lambda path_type, platform: _paths(path_type, platform), use_cache=True)
    OmegaConf.register_new_resolver("lower", lambda key: _lower(key))


def get_configuration_files_from_namespace(namespace: str="ftrack.library") -> list[Path]:
    configuration_files = []
    root_namespace_package = importlib.import_module(namespace)
    packages = pkgutil.walk_packages(root_namespace_package.__path__, prefix=root_namespace_package.__name__ + ".")

    for package in packages:
        module_spec = package.module_finder.find_spec(package.name)
        # check if this is a package (non-packages will have a submodule_search_locations attribute of None)
        if module_spec.submodule_search_locations and module_spec.name.split(".")[-1] == "configuration":
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

def interpolate_configuration_values():
    pass

def inject_builtin_configuration_values():
    # TODO: This might not be needed when using resolvers
    pass

def inject_named_regex_groups():
    pass