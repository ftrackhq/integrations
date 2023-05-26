# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack
import os
import logging
import logging.config
import appdirs
import errno


def get_log_directory():
    '''Get log directory.

    Will create the directory (recursively) if it does not exist.

    Raise if the directory can not be created.
    '''
    user_data_dir = appdirs.user_data_dir('ftrack-connect', 'ftrack')
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
    logger_name, level=None, format=None, extra_modules=None
):
    '''Configure `loggerName` loggers with console and file handler.

    Optionally specify log *level* (default WARNING)

    Optionally set *format*, default:
    `%(asctime)s - %(name)s - %(levelname)s - %(message)s`.

    Optional *extra_modules* to extend the modules to be set to *level*.
    '''

    # Provide default values for level and format.
    format = (
        format
        or '%(levelname)s - %(threadName)s - %(asctime)s - %(name)s - %(message)s'
    )
    level = level or logging.WARNING

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

    # Cast to list in case is a tuple.
    modules = ['ftrack_api', 'urllib3', 'requests']
    modules.extend(list(extra_modules))

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
        'filters': {'application_launcher_only': {'name': logger_name}},
        'formatters': {'file': {'format': format}},
        'loggers': {
            logger_name: {'level': 'DEBUG', 'handlers': ['console', 'file']}
        },
    }

    for module in modules:
        current_level = level
        logging_settings['loggers'].setdefault(
            module, {'level': current_level}
        )

    # Set default logging settings.
    logging.config.dictConfig(logging_settings)

    # Redirect warnings to log so can be debugged.
    logging.captureWarnings(True)

    # Log out the file output.
    logging.info('Saving log file to: {0}'.format(logfile))
