# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import logging
import ftrack_api
import time
from ftrack_connect_pipeline import constants
from ftrack_connect_pipeline import exception
from ftrack_connect_pipeline_qt.client.widgets import BaseWidget
from ftrack_connect_pipeline import plugin


class BasePluginWidget(plugin._Base):
    type = 'widget'
    return_type = BaseWidget

    def _base_topic(self, topic):
        required = [
            self.host,
            self.type,
            self.plugin_type,
            self.plugin_name,
            self.ui
        ]

        if not all(required):
            raise exception.PluginError('Some required fields are missing')

        topic = constants.WIDGET_EVENT.format(
            topic,
            self.host,
            self.ui,
            self.type,
            self.plugin_type,
            self.plugin_name
        )
        return topic

class ContextWidget(BasePluginWidget):
    plugin_type = constants.CONTEXT


from ftrack_connect_pipeline_qt.plugin.load import *
from ftrack_connect_pipeline_qt.plugin.publish import *
