# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

from ftrack_connect_pipeline import exception
from ftrack_connect_pipeline import plugin
from ftrack_connect_pipeline_qt import constants
from ftrack_connect_pipeline_qt.client.widgets import BaseWidget


class BasePluginWidget(plugin.BasePlugin):
    type = 'widget'
    return_type = BaseWidget
    ui = constants.UI

    def _base_topic(self, topic):
        '''Ensures that we pass all the needed information to the topic
        with *topic*.

        *topic* topic base value

        Return formated topic

        Raise :exc:`ftrack_connect_pipeline.exception.PluginError` if some
        information is missed.
        '''
        required = [
            self.host,
            self.type,
            self.plugin_type,
            self.plugin_name,
            self.ui
        ]

        if not all(required):
            raise exception.PluginError('Some required fields are missing')

        topic = (
            'topic={} and data.pipeline.host={} and data.pipeline.ui={} '
            'and data.pipeline.type={} and data.pipeline.plugin_type={} '
            'and data.pipeline.plugin_name={}'
        ).format(
            topic, self.host, self.ui, self.type,
            self.plugin_type, self.plugin_name
        )
        return topic



from ftrack_connect_pipeline_qt.plugin.collector import *
from ftrack_connect_pipeline_qt.plugin.context import *
from ftrack_connect_pipeline_qt.plugin.finaliser import *
from ftrack_connect_pipeline_qt.plugin.output import *
from ftrack_connect_pipeline_qt.plugin.validator import *
