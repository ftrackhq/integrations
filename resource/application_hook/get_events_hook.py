# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

import logging

import ftrack
import ftrack_api

log = logging.getLogger(__name__)


def callback(event):
    '''Handle get events callback.'''
    log.warning('Get events!')

    session = ftrack_api.Session()

    context = event['data']['context']
    cases = []
    events = []

    if context['task']:

        cases.append(
            '(feeds.owner_id in ({task_ids}) and action is '
            '"asset.published")'.format(
                task_ids=','.join(context['task'])
            )
        )

        cases.append(
            'parent_id in ({task_ids}) and action like '
            '"change.status.%"'.format(
                task_ids=','.join(context['task'])
            )
        )

        cases.append(
            '(parent_id in ({task_ids}) and action in '
            '("update.custom_attribute.fend", "update.custom_attribute.fstart"))'.format(
                task_ids=','.join(context['task'])
            )
        )

    if cases:
        events = session.query(
            'select id, action, parent_id, parent_type, created_at, data '
            'from Event where {0}'.format(' or '.join(cases))
        ).all()

        events.sort(key=lambda event: event['created_at'], reverse=True)

    return events


def register(registry, **kw):
    '''Register hook.'''

    # Validate that registry is instance of ftrack.Registry, if not
    # return early since the register method probably is called
    # from the new API.
    if not isinstance(registry, ftrack.Registry):
        return

    ftrack.EVENT_HUB.subscribe(
        'topic=ftrack.crew.notification.get-events',
        callback
    )
