# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import functools
import platform
import sys
import logging
import inspect

logger = logging.getLogger('ftrack_utils:usage')


def track_framework_usage(event_name, metadata, kwarg_mapping_list=[]):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            from ftrack_utils.usage import (
                get_usage_tracker,
                set_usage_tracker,
                UsageTracker,
            )

            # Ensure UsageTracker is set and available
            usage_tracker = get_usage_tracker()
            if not usage_tracker:
                logger.warning(
                    "UsageTracker instance is not set. Try to initialize a default one."
                )
                # Try to instantiate UsageTracker if class has session
                try:
                    if args and hasattr(args[0], '__class__'):
                        instance = args[0]
                        if hasattr(instance, 'session'):
                            session = getattr(instance, 'session')
                        else:
                            return AttributeError(
                                "The 'session' property is required to initialize UsageTracker but "
                                "not found in the class. Skipping initialization as can't track usage."
                            )

                        # Determine the module and method name
                        full_module_name = func.__module__
                        # Extract the root module name
                        root_module_name = full_module_name.split('.')[0]
                        method_name = func.__name__

                        # Retrieve the root module and its version
                        module = sys.modules[root_module_name]

                        library_version = '0.0.0'
                        if hasattr(module, '__version__'):
                            library_version = module.__version__
                        else:
                            logger.warning(
                                f"The root module {root_module_name} does not have a "
                                f"'__version__' attribute. Setting 0.0.0 as default version."
                            )

                        # Get the current OS platform
                        current_os = platform.system()

                        # Setup metadata
                        default_metadata = dict(
                            module_name=root_module_name,
                            version=library_version,
                            os=current_os,
                        )
                        # Set the Usage tracker
                        set_usage_tracker(
                            UsageTracker(
                                session=session, default_data=default_metadata
                            )
                        )

                except Exception as e:
                    logger.error(e)

                finally:
                    usage_tracker = get_usage_tracker()

            # Get the function's argument names and values
            func_args = inspect.signature(func).parameters
            arg_names = list(func_args.keys())

            # Build a dictionary of argument names and values
            arg_values = args + tuple(kwargs.values())
            args_metadata = dict(zip(arg_names, arg_values))

            # Update metadata with function arguments if specified in kwarg_mapping_list
            for key in kwarg_mapping_list:
                if key in args_metadata:
                    metadata[key] = args_metadata[key]
                else:
                    logger.warning(
                        f'Provided kwarg mapping {key} seems to not '
                        f'exists as argument of this function'
                    )

            if usage_tracker:
                usage_tracker.track(event_name, metadata)

            # Call the original function
            return func(*args, **kwargs)

        return wrapper

    return decorator
