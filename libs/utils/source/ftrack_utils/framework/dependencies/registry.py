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


def scan_modules(extension_types, package_names):
    registry_result = {}
    # Look in all the depenency packages in the current python environment
    for package in pkgutil.iter_modules():
        # Pick only the that matches ftrack framework and the module type
        if package.name not in package_names:
            continue

        # Import the register module
        register_module = getattr(
            __import__(package.name, fromlist=['register']), 'register'
        )
        if not register_module:
            logger.error(
                "No register module in package {}".format(package.name)
            )
            continue
        if register_module.EXTENSION_TYPE not in extension_types:
            logger.error(
                "Package type is of {} type({}) is not in the "
                "desired extension_types {}".format(
                    package.name,
                    register_module.EXTENSION_TYPE,
                    extension_types,
                )
            )
            continue

        # Call the register method We pass the event manager
        if not registry_result.get(register_module.EXTENSION_TYPE):
            registry_result[register_module.EXTENSION_TYPE] = []
        result = register_module.register()
        if type(result) == list:
            # Result might be a list so extend the current registry list
            registry_result[register_module.EXTENSION_TYPE].extend(result)
            continue
        # If result is just string, we append it to our registry
        registry_result[register_module.EXTENSION_TYPE].append(result)

    # Return the result
    return registry_result


def register_framework_modules_by_type(event_manager, module_type, callback):
    registry_result = []
    # Look in all the depenency packages in the current python environment
    module_type_composed_name = module_type.split("_")
    for package in pkgutil.iter_modules():
        # Pick only the that matches ftrack framework and the module type
        is_type = all(
            x in package.name.split("_")
            for x in ['ftrack', 'framework'] + module_type_composed_name
        )
        if not is_type:
            continue
        # Import the register module
        register_module = getattr(
            __import__(package.name, fromlist=['register']), 'register'
        )
        # Call the register method We pass the event manager
        result = register_module.register(event_manager)

        if type(result) == list:
            # Result might be a list so extend the current registry list
            registry_result.extend(result)
            continue
        # If result is just string, we append it to our registry
        registry_result.append(result)

    # Call the callback with the result
    if registry_result:
        callback(registry_result)
    else:
        logger.error(
            "Couldn't find any {} module to register".format(module_type)
        )


def scan_modules_from_directory(class_type, current_dir):
    '''Return available modules on the given directory'''

    subfolders = fast_scandir(current_dir)
    if not subfolders:
        subfolders = [current_dir]
    registered_dependencies = []
    for loader, module_name, is_pkg in pkgutil.walk_packages(subfolders):
        _module = loader.find_module(module_name).load_module(module_name)
        cls_members = inspect.getmembers(_module, inspect.isclass)
        success_registry = False
        for name, obj in cls_members:
            if obj == class_type:
                continue
            if class_type not in inspect.getmro(obj):
                logger.debug(
                    "Not registering {} because it is not type of {}".format(
                        name, class_type
                    )
                )
                continue
            try:
                # Call the register classmethod. We don't init the widget here
                obj.register()
                registered_dependencies.append(obj)
            except Exception as e:
                logger.warning(
                    "Couldn't register dependency {} \n error: {}".format(
                        name, e
                    )
                )
                continue
            logger.debug("Dependency {} registered".format(name))
            success_registry = True

        if not success_registry:
            logger.warning(
                "No framework compatible dependency found in module {} "
                "in path{}".format(module_name, loader.path)
            )
    return registered_dependencies


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
                continue
            try:
                registry_result = obj.register()
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
