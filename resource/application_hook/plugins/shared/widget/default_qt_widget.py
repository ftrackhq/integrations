# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import functools
import logging

import ftrack_api

from ftrack_connect_pipeline import constants

logger = logging.getLogger('ftrack_connect_pipeline.plugin')


def register_widget(session, event):
    from ftrack_connect_pipeline.qt.widgets import simple
    return simple.SimpleWidget(session=session, **event['data']['settings'])


def register(api_object, **kw):
    '''Register plugin to api_object.'''

    # Validate that api_object is an instance of ftrack_api.Session. If not,
    # assume that _register_assets is being called from an incompatible API
    # and return without doing anything.
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return

    plugin_types = [
        constants.VALIDATORS,
        constants.COLLECTORS,
        constants.EXTRACTORS,
        constants.PUBLISHERS,
        constants.IMPORTERS
    ]

    for plugin_type in plugin_types:
        event_handler = functools.partial(
            register_widget, api_object
        )
        api_object.event_hub.subscribe(
            'topic={} and '
            'data.pipeline.ui={} and '
            'data.pipeline.type=widget and '
            'data.pipeline.plugin_type={} and '
            'data.pipeline.plugin_name={}'.format(
                constants.PIPELINE_REGISTER_TOPIC,
                constants.UI,
                plugin_type,
                'default.widget'
            ),
            event_handler
        )
