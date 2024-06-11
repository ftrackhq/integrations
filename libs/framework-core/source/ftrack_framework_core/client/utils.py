# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack


def run_in_main_thread(func):
    def wrapper(*args, **kwargs):
        from ftrack_framework_core.client import Client

        if Client.static_properties().get('run_in_main_thread_wrapper'):
            return Client.static_properties()['run_in_main_thread_wrapper'](
                func
            )(*args, **kwargs)
        return func(*args, **kwargs)

    return wrapper