# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

from ftrack_connect_pipeline_3dsmax import plugin
from ftrack_connect_pipeline_qt.plugin.widget.base_collector_widget import (
    BaseCollectorWidget,
)

import ftrack_api


class MaxGeometryPublisherCollectorOptionsWidget(BaseCollectorWidget):
    '''Max geometry collector widget plugin'''

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
        super(MaxGeometryPublisherCollectorOptionsWidget, self).__init__(
            parent=parent,
            session=session,
            data=data,
            name=name,
            description=description,
            options=options,
            context_id=context_id,
            asset_type_name=asset_type_name,
        )


class MaxGeometryPublisherCollectorPluginWidget(
    plugin.MaxPublisherCollectorPluginWidget
):
    plugin_name = 'max_geometry_publisher_collector'
    widget = MaxGeometryPublisherCollectorOptionsWidget


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = MaxGeometryPublisherCollectorPluginWidget(api_object)
    plugin.register()
