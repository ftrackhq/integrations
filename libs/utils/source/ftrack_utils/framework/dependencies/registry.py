# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import pkgutil
import logging
import inspect
import glob
import os
import json

from ftrack_utils.directories.scan_dir import fast_scandir

logger = logging.getLogger(__name__)


def get_framework_extensions_from_directory(scan_dir):
    '''Return available extensions on the given directory'''
    subfolders = fast_scandir(scan_dir)
    if not subfolders:
        subfolders = [scan_dir]

    available_extensions = []
    # Check non python extensions
    # TODO: refactor this part once all tool-configs are converted to yml files
    for _dir in subfolders:
        json_pattern = os.path.join(_dir, '*.json')
        file_list = glob.glob(json_pattern)
        if not file_list:
            continue
        success_registry = False
        for _file in file_list:
            with open(_file) as json_file:
                data = json.load(json_file)
                if data.get("tool_type"):
                    registry_result = {
                        "extension_type": "tool_config",
                        "name": data.get("tool_title"),
                        "cls": _file,
                    }
                    available_extensions.append(registry_result)
                    success_registry = True
                    continue
                if data.get("$schema"):
                    registry_result = {
                        "extension_type": "schema",
                        "name": data.get("title"),
                        "cls": _file,
                    }
                    available_extensions.append(registry_result)
                    success_registry = True
                    continue
        if not success_registry:
            logger.warning(
                "No framework compatible json extension found in "
                "folder {}".format(_dir)
            )

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
                if {"name", "extension_type", "cls"} != registry_result.keys():
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
                "No framework compatible python extension found in module {} "
                "from path{}".format(module_name, loader.path)
            )

    return available_extensions
