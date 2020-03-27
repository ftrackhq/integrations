
# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

from ftrack_connect_pipeline_qt.client.widgets.options import (
    dynamic as dynamic_widget
)
from ftrack_connect_pipeline_qt.plugin import BasePluginWidget


class DefaultWidget(BasePluginWidget):
    plugin_name = 'default.widget'
    plugin_type = '*'
    widget = dynamic_widget.DynamicWidget


def register(api_object, **kw):
    plugin = DefaultWidget(api_object)
    plugin.register()
