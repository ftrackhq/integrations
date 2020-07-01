
# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

from ftrack_connect_pipeline_qt import plugin
from ftrack_connect_pipeline_qt.client.widgets.options import (
    context as context_widget
)
import ftrack_api


class ContextWidget(plugin.LoaderContextWidget):
    plugin_name = 'context.load'
    widget = context_widget.LoadContextWidget


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = ContextWidget(api_object)
    plugin.register()
