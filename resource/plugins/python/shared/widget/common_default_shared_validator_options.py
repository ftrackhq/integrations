# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

from ftrack_connect_pipeline_qt.plugin.widget import dynamic as dynamic_widget
from ftrack_connect_pipeline_qt import plugin
import ftrack_api


class CommonDefaultSharedValidatorOptionsWidget(dynamic_widget.DynamicWidget):
    '''Shared/fallback dynamic validator options user input plugin widget'''

    enable_run_plugin = False

    def __init__(
        self,
        parent=None,
        context_id=None,
        asset_type_name=None,
        session=None,
        data=None,
        name=None,
        description=None,
        options=None,
    ):
        '''initialise CommonDefaultPublisherCollectorOptionsWidget with *parent*, *session*, *data*,
        *name*, *description*, *options*
        '''
        super(CommonDefaultSharedValidatorOptionsWidget, self).__init__(
            parent=parent,
            context_id=context_id,
            asset_type_name=asset_type_name,
            session=session,
            data=data,
            name=name,
            description=description,
            options=options,
        )


class CommonDefaultSharedValidatorPluginWidget(
    plugin.PublisherValidatorPluginWidget
):
    plugin_name = 'common_default_shared_validator'
    widget = CommonDefaultSharedValidatorOptionsWidget


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = CommonDefaultSharedValidatorPluginWidget(api_object)
    plugin.register()
