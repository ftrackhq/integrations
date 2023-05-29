# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack
import os
import logging
import logging.config
import appdirs
import functools
import errno

_logger_name = None

def report_exception(function):
    """
    A decorator that wraps the passed in function and logs
    exceptions should one occur
    # https://www.blog.pythonlibrary.org/2016/06/09/python-how-to-create-an-exception-logging-decorator/
    """

    @functools.wraps(function)
    def wrapper(*args, **kwargs):
        global _logger_name
        logger = logging.getLogger(_logger_name)
        try:
            return function(*args, **kwargs)
        except:
            # log the exception
            err = 'Exception cought in : '
            err += function.__name__
            logger.exception(err)

            # re-raise the exception
            raise

    return wrapper


def get_log_directory():
    '''Get log directory.

    Will create the directory (recursively) if it does not exist.

    Raise if the directory can not be created.
    '''

    user_data_dir = appdirs.user_data_dir('ftrack-connect', 'ftrack')
    log_directory = os.path.join(user_data_dir, 'log').encode('utf8')


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
    global _logger_name
    _logger_name = logger_name

    log_directory = get_log_directory()
    logfile = os.path.join(log_directory, '{0}.log'.format(logger_name).encode('utf8')
    )

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
        'formatters': {
            'file': {
                'format': format
            }
        },
        'loggers': {
            '': {
                'level': 'DEBUG',
                'handlers': ['console', 'file']
            },
            'ftrack_api': {
                'level': 'INFO',
            },
            'FTrackCore': {
                'level': 'INFO',
            },
            'Hiero': {
                'level': 'INFO',
            },
            'requests': {
                'level': 'ERROR'
            },
            'urllib3': {
                'level': 'ERROR'
            }
        }
    }

    # Set default logging settings.
    logging.config.dictConfig(logging_settings)

    # Redirect warnings to log so can be debugged.
    logging.captureWarnings(True)

    # Log out the file output.
    logging.info('Saving log file to: {0}'.format(logfile))
