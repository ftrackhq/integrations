# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import logging
import os
import traceback


from ftrack_framework_core.configure_logging import configure_logging

from ftrack_utils.extensions.environment import (
    get_extensions_path_from_environment,
)


# Evaluate version and log package version
try:
    from ftrack_utils.version import get_version

    __version__ = get_version(
        os.path.basename(os.path.dirname(__file__)),
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    )
except Exception:
    __version__ = '0.0.0'

extra_handlers = {
    'maya': {
        'class': 'maya.utils.MayaGuiLogHandler',
        'level': 'INFO',
        'formatter': 'file',
    }
}

configure_logging(
    'ftrack_framework_maya',
    extra_modules=['ftrack_qt'],
    extra_handlers=extra_handlers,
    propagate=False,
)

logger = logging.getLogger(__name__)
logger.debug('v{}'.format(__version__))


# TODO: implement menu
def bootstrap_integration(framework_extensions_path):
    pass


def run_integration():
    pass


# Find and read DCC config
try:
    bootstrap_integration(get_extensions_path_from_environment())
    run_integration()
except:
    # Make sure any exception that happens are logged as there is most likely no console
    logger.error(traceback.format_exc())
    raise
