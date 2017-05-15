# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

import logging

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



def register(session, **kw):
    '''Register plugin. Called when used as an plugin.'''
    # Validate that session is an instance of ftrack_api.Session. If not,
    # assume that register is being called from an old or incompatible API and
    # return without doing anything.
    if not isinstance(session, ftrack_api.session.Session):
        return


    session.event_hub.subscribe(
        'topic=ftrack.crew.notification.get-events',
        callback
    )


