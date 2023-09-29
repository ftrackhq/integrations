# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import os
import sys


def scan_modules():
    result = []
    for path in sys.path:
        if os.path.exists(path):
            for fn in os.listdir(path):
                if fn.find('-') > -1:
                    continue
                result.append(fn.lower())
    return result


def scan_framework_modules():
    return [
        fn
        for fn in scan_modules()
        if fn.startswith('ftrack_framework')
        or fn in ['ftrack_utils', 'ftrack_constants']
    ]
