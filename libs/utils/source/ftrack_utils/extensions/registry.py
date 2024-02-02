# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import pkgutil
import logging
import inspect
import glob
import os
import yaml
import re

from ftrack_utils.directories.scan_dir import fast_scandir

logger = logging.getLogger(__name__)

env_matcher = re.compile(r'\$\{([^}^{]+)}')


# Patch yaml module to support environment variable substitution
def env_constructor(loader, node):
    '''Extract the matched value, expand env variable, and replace the match.'''
    value = node.value
    match = env_matcher.match(value)
    env_var = match.group()[2:-1]
    return os.environ.get(env_var, '') + value[match.end() :]


yaml.add_implicit_resolver('!env', env_matcher, None, yaml.SafeLoader)
yaml.add_constructor('!env', env_constructor, yaml.SafeLoader)


def register_yaml_files(file_list):
    '''
    Generate data registry files for all extension compatible .yaml files in
    the given *file_list*. Support environment variable substitution in the yaml file.
    '''

    registered_files = []
    for _file in file_list:
        with open(_file, 'r') as yaml_file:
            try:
                yaml_content = yaml.safe_load(yaml_file)
            except yaml.YAMLError as exc:
                # Log an error if the yaml file is invalid.
                logger.error(
                    "Invalid .yaml file\nFile: {}\nError: {}".format(
                        _file, exc
                    )
                )
                continue
            if not yaml_content.get("type"):
                # Log warning if yaml file doesn't contain type key.
                logger.warning(
                    "No extension compatible .yaml file, missing 'type'."
                    "\nFile: {}".format(_file)
                )
                continue
            data = {
                "extension_type": yaml_content['type'],
                "name": yaml_content['name'],
                "extension": yaml_content,
                "path": _file,
            }
            registered_files.append(data)
    return registered_files


def get_files_from_folder(_dir, filetype_pattern):
    '''
    Return all files matching the *filetype_pattern* the given folder *_dir*
    '''
    pattern = os.path.join(_dir, filetype_pattern)
    file_list = glob.glob(pattern)
    if not file_list:
        return None
    return file_list


def get_extensions_from_directory(scan_dir):
    '''Return available extensions on the given directory'''
    subfolders = fast_scandir(scan_dir)
    if not subfolders:
        subfolders = [scan_dir]
    else:
        # Add  the original path to the list of paths
        subfolders.append(scan_dir)

    available_extensions = []
    # Check non python extensions
    for _dir in subfolders:
        file_list = get_files_from_folder(_dir, filetype_pattern="*.y*ml")
        if not file_list:
            continue
        registered_files = register_yaml_files(file_list)
        if not registered_files:
            logger.warning(
                "No compatible yaml extensions found in "
                "folder {}".format(_dir)
            )
        available_extensions.extend(registered_files)

    for loader, module_name, is_pkg in pkgutil.walk_packages(subfolders):
        _module = loader.find_module(module_name).load_module(module_name)
        cls_members = inspect.getmembers(_module, inspect.isclass)
        success_registry = False
        for name, obj in cls_members:
            if obj.__module__ != _module.__name__:
                # We just want to check the current module, not the imported or
                # inherited classes
                continue
            try:
                registry_result = obj.register()
                # Validate registry
                if {
                    "name",
                    "extension_type",
                    "extension",
                    "path",
                } != registry_result.keys():
                    raise ValueError(
                        "The register function did not match expected format:"
                        " {0}".format(registry_result.keys())
                    )
                available_extensions.append(registry_result)
                success_registry = True
            except Exception as e:
                logger.warning(
                    "Couldn't register extension {} \n error: {}".format(
                        name, e
                    )
                )
                continue
        if not success_registry:
            logger.warning(
                "No compatible python extension found in module {} "
                "from path{}".format(module_name, loader.path)
            )

    return available_extensions
