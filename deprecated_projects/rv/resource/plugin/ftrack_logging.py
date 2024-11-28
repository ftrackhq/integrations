# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack
import os
import logging
import logging.config
import errno
import tempfile


def get_log_directory():
    '''Get log directory.

    Will create the directory (recursively) if it does not exist.

    Raise if the directory can not be created.
    '''
    try:
        import platformdirs  # Inline import to avoid RV crashing if not available.

        user_data_dir = platformdirs.user_data_dir('ftrack-connect', 'ftrack')
        log_directory = os.path.join(user_data_dir, 'log')
    except Exception:
        log_directory = tempfile.mkdtemp()

    if not os.path.exists(log_directory):
        try:
            os.makedirs(log_directory)
        except OSError as error:
            if error.errno == errno.EEXIST and os.path.isdir(log_directory):
                pass
            else:
                raise

    return log_directory


def configure_logging(logger_name, level=None, format=None):
    '''Configure `loggerName` loggers with console and file handler.

    Optionally specify log *level* (default WARNING)

    Optionally set *format*, default:
    `%(asctime)s - %(name)s - %(levelname)s - %(message)s`.
    '''

    # provide default values for level and format
    format = format or '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    level = level or logging.WARNING

    log_directory = get_log_directory()
    logfile = os.path.join(log_directory, '{0}.log'.format(logger_name))

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
        'formatters': {'file': {'format': format}},
        'loggers': {
            '': {'level': 'DEBUG', 'handlers': ['console', 'file']},
            'ftrack_api': {
                'level': 'INFO',
            },
            'FTrackCore': {
                'level': 'INFO',
            },
        },
    }

    # Set default logging settings.
    logging.config.dictConfig(logging_settings)

    # Redirect warnings to log so can be debugged.
    logging.captureWarnings(True)

    # Log out the file output.
    logging.info('Saving log file to: {0}'.format(logfile))
