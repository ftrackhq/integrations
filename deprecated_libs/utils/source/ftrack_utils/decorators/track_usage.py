# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import functools
import platform
import sys
import logging
import inspect

logger = logging.getLogger('ftrack_utils:usage')


def track_framework_usage(event_name, metadata, tracked_args=None):
    """
    Decorator to track usage of framework functions.

    This decorator wraps a function to track its usage along with specified metadata and arguments. It ensures that a
    UsageTracker instance is set and available. If not, it attempts to initialize a default one using the session
    attribute of the first argument of the wrapped function, which is expected to be an instance of a class with a
    session attribute.

    Parameters:
    *event_name* (str): The name of the event to track.
    *metadata* (dict): A dictionary of metadata to track along with the event. This can include any relevant
    information about the event.
    *tracked_args* (list): A list of argument names (as strings) of the wrapped function whose values should be
    included in the metadata. Defaults to an empty list.

    The decorator updates the metadata dictionary with the values of the specified arguments (if present) before
    tracking the event. It logs a warning if a specified argument name does not exist in the function's arguments.

    If the UsageTracker cannot be initialized (e.g., due to the absence of a session attribute), it logs an error
    and skips tracking.

    Usage:
    @track_framework_usage('event_name', {'key': 'value'}, ['arg1', 'arg2'])
    def some_function(arg1, arg2):
        pass

    This will track the usage of `some_function`, including the values of `arg1` and `arg2` in the metadata.

    Returns:
    The original function wrapped with usage tracking functionality.
    """

    if not tracked_args:
        tracked_args = []

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

            # Get the function's signature
            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()

            # Build a dictionary of argument names and their bound values
            args_metadata = bound_args.arguments

            # Update metadata with function arguments if specified in kwarg_mapping_list
            for key in tracked_args:
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
