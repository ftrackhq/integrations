# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import functools
import logging

import ftrack_api

from ftrack_connect_pipeline import constants

logger = logging.getLogger('ftrack_connect_pipeline.plugin')


def register_widget(session, event):
    from ftrack_connect_pipeline.qt.widgets import context
    return context.PublishContextWidget(session=session, **event['data']['settings'])


def register(api_object, **kw):
    '''Register plugin to api_object.'''

    # Validate that api_object is an instance of ftrack_api.Session. If not,
    # assume that _register_assets is being called from an incompatible API
    # and return without doing anything.
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return

    context_topic_qt = constants.CONTEXT_PLUGIN_TOPIC.format('context.publish')

    logger.info('discovering :{}'.format(context_topic_qt))

    event_handler = functools.partial(
        register_widget, api_object
    )
    api_object.event_hub.subscribe(
        'topic={} and data.ui={} and data.type=widget'.format(context_topic_qt, constants.UI),
        event_handler
    )
