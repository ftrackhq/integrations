# :coding: utf-8
# :copyright: Copyright (c) 2014 ftrack

import os
import logging


def setup():
    '''Setup logging for ftrack modules.

    Default to 'debug' level. Check :envvar:`FTRACK_LOG_LEVEL` for override.

    '''
    levels = {}
    for level in (
        logging.NOTSET, logging.DEBUG, logging.INFO,
        logging.WARNING, logging.ERROR, logging.CRITICAL
    ):
        levels[logging.getLevelName(level).lower()] = level

    requestedLevel = os.environ.get('FTRACK_LOG_LEVEL', 'debug').lower()
    try:
        level = levels[requestedLevel]
    except KeyError:
        print(
            'WARNING:ftrack_connect_rv: FTRACK_LOG_LEVEL value "{0}" is '
            'invalid. Should be one of {1}. Forcing to "debug".'
            .format(requestedLevel, ', '.join(levels))
        )
        level = levels['debug']

    logging.basicConfig(level=level)
