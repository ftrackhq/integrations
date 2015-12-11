# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

import logging
import os
import re

import ftrack


FTRACK_CONNECT_PACKAGE_RESOURCE_PATH = os.environ.get(
    'FTRACK_CONNECT_PACKAGE_RESOURCE_PATH',
    os.path.abspath(
        os.path.join(
            os.path.dirname(__file__), '..'
        )
    )
)

VERSION = 'Unknown'
with open(os.path.join(
    FTRACK_CONNECT_PACKAGE_RESOURCE_PATH, 'ftrack_connect_package_version.py'
)) as _version_file:
    VERSION = re.match(
        r'.*__version__ = \'(.*?)\'', _version_file.read(), re.DOTALL
    ).group(1)


def get_version_information(event):
    '''Return version information for ftrack connect package.'''
    return [
        dict(
            name='ftrack connect package',
            version=VERSION,
            core=True
        )
    ]


def register(registry, **kw):
    '''Register version information hook.'''

    logger = logging.getLogger(
        'ftrack_connect_package_version_information:register'
    )

    # Validate that registry is an instance of ftrack.Registry. If not,
    # assume that register is being called from a new or incompatible API and
    # return without doing anything.
    if not isinstance(registry, ftrack.Registry):
        logger.debug(
            'Not subscribing plugin as passed argument {0!r} is not an '
            'ftrack.Registry instance.'.format(registry)
        )
        return

    ftrack.EVENT_HUB.subscribe(
        'topic=ftrack.connect.plugin.debug-information',
        get_version_information
    )
