#! /usr/bin/env python
# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import sys
import os

deps_paths = os.environ.get('PYTHONPATH', '').split(os.pathsep)
for path in deps_paths:
    sys.path.append(path)

from QtExt import QtGui, QtWidgets

import ftrack_api
from ftrack_connect_pipeline import constants
from ftrack_connect_pipeline.client import BaseQtPipelineWidget


class QtPipelinePublishWidget(BaseQtPipelineWidget):

    def __init__(self, ui, host, parent=None):
        super(QtPipelinePublishWidget, self).__init__(ui, host, parent=parent)
        self.setWindowTitle('Standalone Pipeline Publisher')

        publisher_event = ftrack_api.event.base.Event(
            topic=constants.PIPELINE_DEFINITION_TOPIC,
            data={
                'pipeline': {
                    'type': "publisher"
                }
            }
        )
        self.event_manager.publish(publisher_event, self.on_publishers_loaded)

    def post_build(self):
        super(QtPipelinePublishWidget, self).post_build()
        self.combo.currentIndexChanged.connect(self._on_publisher_changed)

    def on_publishers_loaded(self, event):
        for item_name, item in event['data'].items():
            self.combo.addItem(item_name, item)

    def _on_publisher_changed(self, index):
        '''Slot triggered on asset type change.'''
        self.resetLayout(self.task_layout)

        package_publisher = self.combo.itemData(index)

        contexts = package_publisher['context']
        components = package_publisher['components']

        for context in contexts:
            context_plugin = context
            context_widget = self.fetch_widget(context_plugin, 'context')
            self.logger.info('context_widget: {}'.format(context_widget))

        for component_name, component_stages in components.items():
            for stage_name, stage_plugins in component_stages.items():
                for stage_plugin in stage_plugins:
                    stage_widget = self.fetch_widget(stage_plugin, stage_name)
                    self.logger.info('{}::{}_widget: {}'.format(component_name, stage_name, stage_widget))

        # self._current_asset_type = package['type']
        #
        # stages = asset_schema[self.stages_manager.type]['plugins']
        # for stage in stages:
        #     for current_stage, current_plugins in stage.items():
        #         base_topic = self.stages_manager.stages.get(current_stage)
        #         if not base_topic:
        #             self.logger.warning('stage {} cannot be evaluated'.format(current_stage))
        #             continue
        #
        #         box = QtWidgets.QGroupBox(current_stage)
        #         plugin_layout = QtWidgets.QVBoxLayout()
        #         box.setLayout(plugin_layout)
        #
        #         self.stages_manager.widgets.setdefault(current_stage, [])
        #
        #         for plugin in current_plugins:
        #             widget = self.fetch_widget(plugin, current_stage)
        #             if widget:
        #                 widget_is_visible = plugin.get('visible', True)
        #                 if not widget_is_visible:
        #                     widget.setVisible(False)
        #
        #                 plugin_layout.addWidget(widget)
        #                 self.stages_manager.widgets[current_stage].append(
        #                     (widget, plugin)
        #                 )
        #
        #         self.task_layout.addWidget(box)


if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    wid = QtPipelinePublishWidget(ui=constants.UI, host=constants.HOST)
    wid.show()
    sys.exit(app.exec_())
