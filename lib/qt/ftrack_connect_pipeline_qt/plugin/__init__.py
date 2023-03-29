# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

from ftrack_connect_pipeline import exception
from ftrack_connect_pipeline import plugin
from ftrack_connect_pipeline_qt import constants as qt_constants
from ftrack_connect_pipeline_qt.plugin.widget import BaseOptionsWidget


class BasePluginWidget(plugin.BasePlugin):
    '''Base Class to represent a Widget'''

    category = 'plugin.widget'
    '''Category of the plugin (plugin, plugin.widget...)'''
    return_type = BaseOptionsWidget
    '''Required return type'''
    ui_type = qt_constants.UI_TYPE
    '''Ui tipe of the widget (qt,....)'''
    widget = None
    '''The current widget'''

    def _base_topic(self, topic):
        '''
        Ensures that :attr:`host_type`, :attr:`category`, :attr:`plugin_type`,
        :attr:`plugin_name` and :attr:`ui_type` are defined and Returns a formatted topic of an event
        for the given *topic*

        *topic* topic base value

        Raise :exc:`ftrack_connect_pipeline.exception.PluginError` if some
        information is missed.
        '''
        required = [
            self.host_type,
            self.category,
            self.plugin_type,
            self.plugin_name,
            self.ui_type,
        ]

        if not all(required):
            raise exception.PluginError('Some required fields are missing')

        topic = (
            'topic={} and data.pipeline.host_type={} and data.pipeline.ui_type={} '
            'and data.pipeline.category={} and data.pipeline.plugin_type={} '
            'and data.pipeline.plugin_name={}'
        ).format(
            topic,
            self.host_type,
            self.ui_type,
            self.category,
            self.plugin_type,
            self.plugin_name,
        )
        return topic

    def run(
        self,
        context_id=None,
        asset_type_name=None,
        data=None,
        name=None,
        description=None,
        options=None,
    ):
        return self.widget(
            context_id=context_id,
            asset_type_name=asset_type_name,
            session=self.session,
            data=data,
            name=name,
            description=description,
            options=options,
        )


from ftrack_connect_pipeline_qt.plugin.load import *
from ftrack_connect_pipeline_qt.plugin.open import *
from ftrack_connect_pipeline_qt.plugin.publish import *
