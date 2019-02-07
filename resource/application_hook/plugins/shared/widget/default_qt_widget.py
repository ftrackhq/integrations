# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import functools
import logging

import ftrack_api

from ftrack_connect_pipeline import constants
from ftrack_connect_pipeline.qt.widgets import simple

logger = logging.getLogger(__name__)


def register_widget(session, event):
    return simple.SimpleWidget(session=session, **event['data'])


def register(api_object, **kw):
    '''Register plugin to api_object.'''

    # Validate that api_object is an instance of ftrack_api.Session. If not,
    # assume that _register_assets is being called from an incompatible API
    # and return without doing anything.
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return

    # Register for Qt based integrations
    default_widget_qt = 'default.widget.qt'

    # publisher
    validator_topic_qt = constants.VALIDATORS_PLUGIN_TOPIC.format(default_widget_qt)
    collector_topic_qt = constants.COLLECTORS_PLUGIN_TOPIC.format(default_widget_qt)
    extractor_topic_qt = constants.EXTRACTORS_PLUGIN_TOPIC.format(default_widget_qt)
    publisher_topic_qt = constants.PUBLISHERS_PLUGIN_TOPIC.format(default_widget_qt)

    # loader
    components_topic_qt = constants.COMPONENTS_PLUGIN_TOPIC.format(default_widget_qt)
    importers_topic_qt = constants.IMPORTERS_PLUGIN_TOPIC.format(default_widget_qt)

    # collect all topics
    topics = [
        validator_topic_qt, collector_topic_qt, extractor_topic_qt,
        publisher_topic_qt, components_topic_qt, importers_topic_qt,
    ]

    for topic in topics:
        logger.info('discovering :{}'.format(topic))

        event_handler = functools.partial(
            register_widget, api_object
        )
        api_object.event_hub.subscribe(
            'topic={}'.format(topic),
            event_handler
        )
