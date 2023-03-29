# :coding: utf-8
# :copyright: Copyright (c) 2014-{{cookiecutter.year}} ftrack

from ftrack_connect_pipeline_{{cookiecutter.host_type}} import plugin
from ftrack_connect_pipeline_qt.plugin.widget.base_collector_widget import (
    BaseCollectorWidget,
)

import ftrack_api


class {{cookiecutter.host_type_capitalized}}GenericPublisherCollectorOptionsWidget(BaseCollectorWidget):
    ''' {{cookiecutter.host_type_capitalized}} collector widget plugin'''

    # Run fetch function on widget initialization
    auto_fetch_on_init = True

    def __init__(
        self,
        parent=None,
        session=None,
        data=None,
        name=None,
        description=None,
        options=None,
        context_id=None,
        asset_type_name=None,
    ):
        super({{cookiecutter.host_type_capitalized}}GenericPublisherCollectorOptionsWidget, self).__init__(
            parent=parent,
            session=session,
            data=data,
            name=name,
            description=description,
            options=options,
            context_id=context_id,
            asset_type_name=asset_type_name,
        )


class {{cookiecutter.host_type_capitalized}}GenericPublisherCollectorPluginWidget(
    plugin.{{cookiecutter.host_type_capitalized}}PublisherCollectorPluginWidget
):
    plugin_name = '{{cookiecutter.host_type}}_generic_publisher_collector'
    widget = {{cookiecutter.host_type_capitalized}}GenericPublisherCollectorOptionsWidget


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = {{cookiecutter.host_type_capitalized}}GenericPublisherCollectorPluginWidget(api_object)
    plugin.register()
