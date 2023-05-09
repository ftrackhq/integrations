# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

from ftrack_connect_pipeline_qt.plugin.widget import dynamic as dynamic_widget
from ftrack_connect_pipeline_qt.plugin import BasePluginWidget
import ftrack_api


class CommonDefaultSharedPluginWidget(BasePluginWidget):
    '''Default shared/fallback dynamic user input plugin widget'''

    plugin_name = 'common_default_shared'
    plugin_type = '*'
    widget = dynamic_widget.DynamicWidget


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = CommonDefaultSharedPluginWidget(api_object)
    plugin.register()
