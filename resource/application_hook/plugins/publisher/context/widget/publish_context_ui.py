import functools
import logging

import ftrack_api

from ftrack_connect_pipeline import constants
from ftrack_connect_pipeline.qt.widgets import context

logger = logging.getLogger(__name__)


def register_widget(session, event):
    return context.PublishContextWidget(session=session, **event['data'])


def register(api_object, **kw):
    '''Register plugin to api_object.'''

    # Validate that api_object is an instance of ftrack_api.Session. If not,
    # assume that register_assets is being called from an incompatible API
    # and return without doing anything.
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return

    context_topic_qt = constants.CONTEXT_PLUGIN_TOPIC.format('context.publish.widget.qt')
    context_topic_maya = constants.CONTEXT_PLUGIN_TOPIC.format('context.publish.widget.maya')

    topics = [context_topic_qt, context_topic_maya]

    for context_topic in topics:
        logger.info('discovering :{}'.format(context_topic))

        event_handler = functools.partial(
            register_widget, api_object
        )
        api_object.event_hub.subscribe(
            'topic={}'.format(context_topic),
            event_handler
        )
