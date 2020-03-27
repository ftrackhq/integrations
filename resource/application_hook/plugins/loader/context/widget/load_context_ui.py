
# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

from ftrack_connect_pipeline_qt import plugin
from ftrack_connect_pipeline_qt.client.widgets.options import (
    context as context_widget
)


class ContextWidget(plugin.ContextWidget):
    plugin_name = 'context.load'
    widget = context_widget.LoadContextWidget


def register(api_object, **kw):
    plugin = ContextWidget(api_object)
    plugin.register()
