# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack
import threading
from functools import wraps

# Dock widget in {{ cookiecutter.integration_name.capitalize() }}
def dock_{{ cookiecutter.integration_name }}_right(widget):
    '''Dock *widget* to the right side of {{ cookiecutter.integration_name.capitalize() }}.'''
    pass


def run_in_main_thread(f):
    '''Make sure a function runs in the main {{ cookiecutter.integration_name.capitalize() }} thread.'''

    @wraps(f)
    def decorated(*args, **kwargs):
        if threading.currentThread().name != 'MainThread':
            pass
            # return {{ cookiecutter.integration_name }}_utils.executeInMainThreadWithResult(f, *args, **kwargs)
        else:
            return f(*args, **kwargs)

    return decorated
