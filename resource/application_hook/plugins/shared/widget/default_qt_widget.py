
# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

from ftrack_connect_pipeline_qt.client.widgets import dynamic as dynamic_widget
from ftrack_connect_pipeline_qt.plugin import BasePluginWidget


class ContextWidget(BasePluginWidget):
    plugin_name = 'default.widget'
    plugin_type = '*'

    def run(self, data=None, name=None, description=None, options=None):
        return dynamic_widget.DynamicWidget(
            session=self.session, data=data, name=name,
            description=description, options=options
        )


def register(api_object, **kw):
    plugin = ContextWidget(api_object)
    plugin.register()
