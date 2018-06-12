# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

from __future__ import absolute_import

import os
import logging as _pythonLogging



def setup():
    '''Setup logging for ftrack modules.

    Default to 'warning' level. Check :envvar:`FTRACK_LOG_LEVEL` for override.

    '''
    levels = {}
    for level in (
        _pythonLogging.NOTSET, _pythonLogging.DEBUG, _pythonLogging.INFO,
        _pythonLogging.WARNING, _pythonLogging.ERROR, _pythonLogging.CRITICAL
    ):
        levels[_pythonLogging.getLevelName(level).lower()] = level

    requestedLevel = os.environ.get('FTRACK_LOG_LEVEL', 'warning').lower()
    try:
        level = levels[requestedLevel]
    except KeyError:
        print(
            'WARNING:ftrack_connect_nuke_studio: FTRACK_LOG_LEVEL value "{0}" is '
            'invalid. Should be one of {1}. Forcing to "warning".'
            .format(requestedLevel, ', '.join(levels))
        )
        level = levels['warning']

    # Customise root ftrack logger. This is needed as, by default, The Foundry
    # does not output any logging and also provides no easy way to configure
    # Python logging. Note that adding this handler does make it harder to
    # customise ftrack logging at a global level.
    ftrackLogger = _pythonLogging.getLogger('ftrack_connect_nuke_studio')
    ftrackLogger.setLevel(level)
    ftrackLogger.propagate = False

    streamHandler = _pythonLogging.StreamHandler()
    formatter = _pythonLogging.Formatter('%(levelname)s:%(name)s:%(message)s')
    streamHandler.setFormatter(formatter)
    ftrackLogger.addHandler(streamHandler)