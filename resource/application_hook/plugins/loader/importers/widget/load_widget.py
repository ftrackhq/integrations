# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

from ftrack_connect_pipeline_qt import plugin
from ftrack_connect_pipeline_qt.client.widgets.options import load_widget
import ftrack_api


class LoadBasePluginWidget(plugin.LoaderImporterWidget):
    plugin_name = 'load_base'
    widget = load_widget.LoadBaseWidget


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = LoadBasePluginWidget(api_object)
    plugin.register()
