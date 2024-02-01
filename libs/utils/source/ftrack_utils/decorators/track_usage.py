# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import functools
import platform
import sys
import logging

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
                            label=method_name,
                            module=f"{full_module_name}.{method_name}",
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

            if kwarg_mapping_list:
                for item in kwarg_mapping_list:
                    if item in kwargs.keys():
                        metadata[item] = kwargs[item]
                    else:
                        logger.warning(
                            f'Provided kwarg mapping {item} seems to not '
                            f'exists as argument of this function'
                        )
            if usage_tracker:
                usage_tracker.track(event_name, metadata)

            # Call the original function
            return func(*args, **kwargs)

        return wrapper

    return decorator
