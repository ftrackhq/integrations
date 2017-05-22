# :coding: utf-8
# :copyright: Copyright (c) 2014 ftrack

import os
import tempfile

import ftrack_api
import ftrack_api.accessor.disk
import ftrack_api.entity.location
import ftrack_api.structure.standard


def configure_locations(event):
    session = event['data']['session']

    location = session.ensure(
        'Location', {
            'name': 'studio_default'
        }
    )



    location.priority = 0
    location.structure = ftrack_api.structure.standard.StandardStructure()

    location.accessor = ftrack_api.accessor.disk.DiskAccessor(
        prefix=os.path.expanduser(
            os.getenv(
                'PROJECT_ROOT',
                os.path.join(
                    tempfile.gettempdir(), 'ftrack_connect_nuke_studio_example'
                )
            )
        )
    )




def register(session, **kw):

    # Validate that session is an instance of ftrack_api.Session. If not,
    # assume that register is being called from an incompatible API
    # and return without doing anything.
    if not isinstance(session, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return

    session.event_hub.subscribe(
        'topic=ftrack.api.session.configure-location',
        configure_locations
    )