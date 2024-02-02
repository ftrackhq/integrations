# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import os
import functools
import logging

import ftrack_api
import ftrack_api.accessor.disk

logger = logging.getLogger(
    'com.ftrack.framework-core.tutorial.custom-location-plugin.location.custom_location_plugin'
)


def configure_location(session, event):
    '''Apply our custom structure to default storage scenario location.'''
    import structure

    DEFAULT_USER_DISK_PREFIX = os.path.join(
        os.path.expanduser('~'), 'Documents', 'ftrack_tutorial'
    )

    location = session.pick_location()
    if location['name'] in ['ftrack.unmanaged', 'ftrack.server']:
        location.accessor = ftrack_api.accessor.disk.DiskAccessor(
            prefix=DEFAULT_USER_DISK_PREFIX
        )
    location.structure = structure.Structure()
    # location.priority = 1

    logger.info(
        u'Registered custom file structure at location "{0}", path: {1}.'.format(
            location['name'], DEFAULT_USER_DISK_PREFIX
        )
    )


def register(api_object, **kw):
    '''Register location with *session*.'''

    if not isinstance(api_object, ftrack_api.Session):
        return

    api_object.event_hub.subscribe(
        'topic=ftrack.api.session.configure-location',
        functools.partial(configure_location, api_object),
    )

    api_object.event_hub.subscribe(
        'topic=ftrack.api.connect.configure-location',
        functools.partial(configure_location, api_object),
    )

    logger.info(u'Registered tutorial location plugin.')
