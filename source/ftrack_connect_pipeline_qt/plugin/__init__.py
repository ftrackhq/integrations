# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

from ftrack_connect_pipeline import exception
from ftrack_connect_pipeline import plugin
from ftrack_connect_pipeline_qt import constants
from ftrack_connect_pipeline_qt.client.widgets.options import BaseOptionsWidget


class BasePluginWidget(plugin.BasePlugin):
    type = 'widget'
    return_type = BaseOptionsWidget
    ui_type = constants.UI_TYPE
    widget = None

    def _base_topic(self, topic):
        '''Ensures that we pass all the needed information to the topic
        with *topic*.

        *topic* topic base value

        Return formated topic

        Raise :exc:`ftrack_connect_pipeline.exception.PluginError` if some
        information is missed.
        '''
        required = [
            self.host_type,
            self.type,
            self.plugin_type,
            self.plugin_name,
            self.ui_type
        ]

        if not all(required):
            raise exception.PluginError('Some required fields are missing')

        topic = (
            'topic={} and data.pipeline.host_type={} and data.pipeline.ui_type={} '
            'and data.pipeline.type={} and data.pipeline.plugin_type={} '
            'and data.pipeline.plugin_name={}'
        ).format(
            topic, self.host_type, self.ui_type, self.type,
            self.plugin_type, self.plugin_name
        )
        return topic

    def run(
            self, context=None, data=None, name=None, description=None,
            options=None
    ):
        return self.widget(
            context=context,
            session=self.session, data=data, name=name,
            description=description, options=options
        )


from ftrack_connect_pipeline_qt.plugin.load import *
from ftrack_connect_pipeline_qt.plugin.publish import *
