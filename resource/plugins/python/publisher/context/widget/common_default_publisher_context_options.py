# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

from ftrack_connect_pipeline_qt import plugin
from ftrack_connect_pipeline_qt.plugin.widget import context as context_widget
import ftrack_api


class CommonDefaultPublisherContextPluginWidget(
    plugin.PublisherContextPluginWidget
):
    '''Default publisher context widget enabling user selection'''

    plugin_name = 'common_default_publisher_context'
    widget = context_widget.PublishContextWidget


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = CommonDefaultPublisherContextPluginWidget(api_object)
    plugin.register()
