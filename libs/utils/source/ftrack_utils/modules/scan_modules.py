# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack
import os
import sys
import importlib


def scan_modules():
    '''Scan sys path and return all modules by lower case name.'''
    result = []
    for path in sys.path:
        if os.path.exists(path) and os.path.isdir(path):
            for fn in os.listdir(path):
                if fn.find('-') > -1:
                    continue
                result.append(fn)
    return result


def scan_framework_modules():
    '''Scan sys path for framework modules and return list of module names.'''
    return [
        fn
        for fn in scan_modules()
        if fn.startswith('ftrack_framework')
        or fn in ['ftrack_utils', 'ftrack_constants']
    ]


def load_class_from_module(module_path, class_name):
    '''Load *class_name* of the *module_path*'''
    # Convert file path to module path (assuming it's in the Python path)
    module_name = os.path.splitext(os.path.basename(module_path))[0]

    # Dynamically import the module
    module = importlib.import_module(module_name)

    # Access the class
    cls = getattr(module, class_name)
    return cls
