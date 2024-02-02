# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack
import os
import logging
import logging.config
import sys

import platformdirs
import errno

from ftrack_utils.modules.scan_modules import scan_framework_modules
from ftrack_utils import __version__ as utils_version

from ftrack_framework_core import __version__


def get_log_directory():
    '''Get log directory.

    Will create the directory (recursively) if it does not exist.

    Raise if the directory can not be created.
    '''

    user_data_dir = platformdirs.user_data_dir('ftrack-connect', 'ftrack')
    log_directory = os.path.join(user_data_dir, 'log')

    if not os.path.exists(log_directory):
        try:
            os.makedirs(log_directory)
        except OSError as error:
            if error.errno == errno.EEXIST and os.path.isdir(log_directory):
                pass
            else:
                raise

    return log_directory


def configure_logging(
    logger_name,
    add_extra_framework_modules=True,
    level=None,
    logging_format=None,
    extra_modules=None,
    extra_handlers=None,
    propagate=True,
):
    '''Configure `logger_name` loggers with console and file handler, will scan
    sys path and log framework modules to file if *add_extra_framework_modules* is set
    to true (default).

    Optionally specify log *level* (default WARNING)

    Optionally set *logging_format*, default:
    `%(asctime)s - %(name)s - %(levelname)s - %(message)s`.

    Optional *extra_modules* to extend the modules to be set to *level*.
    '''
    # Provide default values for level and format.
    logging_format = (
        logging_format
        or '%(levelname)s - %(threadName)s - %(asctime)s - %(name)s - %(message)s'
    )
    level = level or logging.INFO

    log_directory = get_log_directory()
    logfile = os.path.join(log_directory, '{0}.log'.format(logger_name))

    # Sanitise the variable, checking the type.
    if not isinstance(extra_modules, (list, tuple, type(None))):
        error_message = (
            'Extra modules: {0} as are not of the correct type.'
            'Expected list or tuple or None, got {1}'.format(
                extra_modules, type(extra_modules)
            )
        )
        raise ValueError(error_message)

    extra_modules = extra_modules or []

    if add_extra_framework_modules:
        # Scan sys path for ftrack_framework* modules to file log
        extra_modules.extend(scan_framework_modules())

    # Cast to list in case is a tuple.
    modules = []
    modules.extend(list(extra_modules))

    extra_handlers = extra_handlers or {}

    logging_settings = {
        'version': 1,
        'disable_existing_loggers': False,
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'level': logging.getLevelName(level),
                'formatter': 'file',
                'stream': 'ext://sys.stdout',
            },
            'file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'level': 'DEBUG',
                'formatter': 'file',
                'filename': logfile,
                'mode': 'a',
                'maxBytes': 10485760,
                'backupCount': 5,
            },
        },
        'formatters': {'file': {'format': logging_format}},
        'loggers': {
            '': {'level': 'INFO', 'handlers': ['console']},
            'ftrack_api': {'level': 'INFO', 'handlers': ['file']},
            'requests': {'level': 'WARNING', 'handlers': ['file']},
            'urllib3': {'level': 'WARNING', 'handlers': ['file']},
        },
    }

    logging_settings['handlers'].update(extra_handlers)

    extra_handlers_names = list(extra_handlers.keys())
    modules_handlers = ['file'] + extra_handlers_names

    for module in modules:
        logging_settings['loggers'].setdefault(
            module,
            {
                'level': 'DEBUG',
                'handlers': modules_handlers,
                'propagate': propagate,
            },
        )

    # Set default logging settings.
    logging.config.dictConfig(logging_settings)

    # Redirect warnings to log so can be debugged.
    logging.captureWarnings(True)

    # Log out the file exporters.
    logging.warning('Saving log file to: {0}'.format(logfile))

    # Log out the version to disk
    logger = logging.getLogger('ftrack_framework_core')
    logger.debug('v{0!s}'.format(__version__))

    # Log utils to disk after logging has been setup.
    logger = logging.getLogger('ftrack_utils')
    logger.debug('v{0!s}'.format(utils_version))
