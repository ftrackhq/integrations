# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

from ftrack_connect_pipeline_maya import plugin
from ftrack_connect_pipeline_qt.plugin.widget.base_collector_widget import (
    BaseCollectorWidget,
)

import ftrack_api


class MayaGenericPublisherCollectorOptionsWidget(BaseCollectorWidget):
    '''Generic/template for Maya publisher collector plugin option user input'''

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
        super(MayaGenericPublisherCollectorOptionsWidget, self).__init__(
            parent=parent,
            session=session,
            data=data,
            name=name,
            description=description,
            options=options,
            context_id=context_id,
            asset_type_name=asset_type_name,
        )


class MayaGenericPublisherCollectorPluginWidget(
    plugin.MayaPublisherCollectorPluginWidget
):
    plugin_name = 'maya_generic_publisher_collector'
    widget = MayaGenericPublisherCollectorOptionsWidget


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = MayaGenericPublisherCollectorPluginWidget(api_object)
    plugin.register()
