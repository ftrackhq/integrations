# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import functools
import platform
import sys
import logging

logger = logging.getLogger('ftrack_utils:usage')


def track_framework_usage(label=None):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            from ftrack_utils.framework.track_usage import (
                ftrack_framework_usage,
            )

            if args and hasattr(args[0], '__class__'):
                instance = args[0]
                if hasattr(instance, 'session'):
                    session = getattr(instance, 'session')
                else:
                    raise AttributeError(
                        "The 'session' property is required to track usage but "
                        "not found in the class."
                    )
            else:
                raise TypeError(
                    "track_framework_usage decorator can only be used on class "
                    "methods."
                )

            # Determine the module and method name
            full_module_name = func.__module__
            # Extract the root module name
            root_module_name = full_module_name.split('.')[0]
            method_name = func.__name__

            # Retrieve the root module and its version
            module = sys.modules[root_module_name]
            if hasattr(module, '__version__'):
                library_version = module.__version__
            else:
                logger.warning(
                    f"The root module {root_module_name} does not have a "
                    f"'__version__' attribute. Setting 0.0.0 as default version."
                )
                library_version = '0.0.0'

            # Use the custom label if provided, otherwise default to method name
            effective_label = label if label else method_name

            # Get the current OS platform
            current_os = platform.system()

            # Call tracking function
            ftrack_framework_usage(
                session,
                effective_label,
                f"{full_module_name}.{method_name}",
                library_version,
                current_os,
            )

            # Call the original function
            return func(*args, **kwargs)

        return wrapper

    return decorator
