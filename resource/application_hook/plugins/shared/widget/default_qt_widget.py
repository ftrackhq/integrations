
# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

from ftrack_connect_pipeline import plugin
from ftrack_connect_pipeline.qt.widgets import simple as simple_widget


class ContextWidget(plugin.BaseWidget):
    plugin_name = 'default.widget'
    plugin_type = '*'

    def run(self, data=None, name=None, description=None, options=None):
        return simple_widget.SimpleWidget(
            session=self.session, data=data, name=name,
            description=description, options=options
        )


def register(api_object, **kw):
    plugin = ContextWidget(api_object)
    plugin.register()
