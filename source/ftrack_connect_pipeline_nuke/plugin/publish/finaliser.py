# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack
import os

from ftrack_connect_pipeline import plugin
from ftrack_connect_pipeline_qt import plugin as pluginWidget
from ftrack_connect_pipeline_nuke.plugin import (
    BaseNukePlugin, BaseNukePluginWidget
)


class PublisherFinaliserNukePlugin(plugin.PublisherFinaliserPlugin, BaseNukePlugin):
    ''' Class representing a Finaliser Plugin

        .. note::

            _required_output is a dictionary containing the 'context_id',
            'asset_name', 'asset_type', 'comment' and 'status_id' of the
            current asset
    '''

    def _run(self, event):
        super_result = super(PublisherFinaliserNukePlugin, self)._run(event)

        data = event['data']['settings']['data']

        for component_name, component_path in data.items():
            os.remove(component_path)

        return super_result


class PublisherFinaliserNukeWidget(
    pluginWidget.PublisherFinaliserWidget, BaseNukePluginWidget
):
    ''' Class representing a Finaliser Widget

        .. note::

            _required_output is a dictionary containing the 'context_id',
            'asset_name', 'asset_type', 'comment' and 'status_id' of the
            current asset
    '''
