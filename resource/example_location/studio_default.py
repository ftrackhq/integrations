# :coding: utf-8
# :copyright: Copyright (c) 2014 ftrack

import os
import tempfile

import ftrack


def register(registry, **kw):
    '''Register location with *registry*.'''
    location_name = 'studio_default'

    ftrack.ensureLocation(location_name)
    structure = ftrack.ClassicStructure()
    accessor = ftrack.DiskAccessor(
        prefix=os.path.expanduser(
            os.getenv(
                'PROJECT_ROOT',
                os.path.join(
                    tempfile.gettempdir(), 'ftrack_connect_nuke_studio_example'
                )
            )
        )
    )

    location = ftrack.Location(
        location_name,
        accessor=accessor,
        structure=structure,
        priority=1
        )

    registry.add(location)
