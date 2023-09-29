# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import pkgutil
import logging
import inspect

from ftrack_utils.directories.scan_dir import fast_scandir

logger = logging.getLogger(__name__)


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


def register_dependencies_from_directory(
    class_type, current_dir, event_manager
):
    '''Register Dependency to api_object.'''

    subfolders = fast_scandir(current_dir)
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
                if obj.register(event_manager) is not False:
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
