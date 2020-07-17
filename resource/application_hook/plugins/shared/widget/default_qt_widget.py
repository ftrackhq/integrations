
# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

from ftrack_connect_pipeline_qt.client.widgets.options import (
    dynamic as dynamic_widget
)
from ftrack_connect_pipeline_qt.plugin import BasePluginWidget
import ftrack_api


class DefaultWidget(BasePluginWidget):
    plugin_name = 'default.widget'
    plugin_type = '*'
    widget = dynamic_widget.DynamicWidget


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = DefaultWidget(api_object)
    plugin.register()
