# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

import urlparse
import pprint

import ftrack_legacy
import ftrack

from FnAssetAPI import logging
import hiero


def callback(event):
    '''Handle version notification call to action.

    The callback will find the track item matching the version in any track
    and switch version.

    '''
    session = ftrack.Session()

    logging.info('Update track to latest versions based on:\n{0}'.format(
        pprint.pformat(event['data']))
    )

    related_components = session.query(
        'select id from Component where '
        'version.asset.versions.id is "{0}"'.format(event['data']['version_id'])
    )

    related_component_ids = [
        component['id'] for component in related_components
    ]
    for item in hiero.core.findItems():

        # Only try to version up track items.
        if isinstance(item, hiero.core.TrackItem):
            
            # User the source to be able to match against entity reference.
            clip = item.source()
            if hasattr(clip, 'entityReference'):
                reference = clip.entityReference()
                if reference and reference.startswith('ftrack://'):

                    # Parse the reference to get the id of the entity.
                    url = urlparse.urlparse(reference)

                    # Check if entityReference is a related component.
                    if url.netloc in related_component_ids:

                        logging.info('Setting new version on "{0}"'.format(
                            str(item)
                        ))

                        # TODO: Set the version more sophisticated based on
                        # version number.
                        item.maxVersion()


def register(registry, **kw):
    '''Register hook.'''

    logging.info('Register version notification hook')

    ftrack_legacy.EVENT_HUB.subscribe(
        'topic=ftrack.crew.notification.version',
        callback
    )
