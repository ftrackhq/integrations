
# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

from ftrack_connect_pipeline_qt.client.widgets.options import (
    dynamic as dynamic_widget
)
from ftrack_connect_pipeline_qt.plugin import BasePluginWidget


class DefaultWidget(BasePluginWidget):
    plugin_name = 'default.widget'
    plugin_type = '*'

    def run(self, context=None, data=None, name=None, description=None, options=None):
        return dynamic_widget.DynamicWidget(
            context=context,
            session=self.session, data=data, name=name,
            description=description, options=options
        )


def register(api_object, **kw):
    plugin = DefaultWidget(api_object)
    plugin.register()
