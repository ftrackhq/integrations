#! /usr/bin/env python
# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import sys
import os
import copy
deps_paths = os.environ.get('PYTHONPATH', '').split(os.pathsep)
for path in deps_paths:
    sys.path.append(path)

from QtExt import QtGui, QtWidgets

import ftrack_api
from ftrack_connect_pipeline import constants
from ftrack_connect_pipeline.client import BaseQtPipelineWidget


class QtPipelinePublishWidget(BaseQtPipelineWidget):

    @property
    def current(self):
        return self._current_publisher

    def __init__(self, ui, host, parent=None):
        super(QtPipelinePublishWidget, self).__init__(ui, host, parent=parent)
        self.setWindowTitle('Standalone Pipeline Publisher')

        self._current_publisher = None

        publisher_event = ftrack_api.event.base.Event(
            topic=constants.PIPELINE_DEFINITION_TOPIC,
            data={
                'pipeline': {
                    'type': "publisher"
                }
            }
        )
        self.event_manager.publish(publisher_event, self.on_publishers_loaded)

    def build(self):
        self.context_layout = QtWidgets.QVBoxLayout()
        self.components_layout = QtWidgets.QVBoxLayout()
        self.publisher_layout = QtWidgets.QVBoxLayout()

        self.task_layout.addLayout(self.context_layout)
        self.task_layout.addLayout(self.components_layout)
        self.task_layout.addLayout(self.publisher_layout)

        self.components_widget = QtWidgets.QTabWidget()
        self.components_layout.addWidget(self.components_widget)

        self.publisher_layout = QtWidgets.QVBoxLayout()
        self.task_layout.addLayout(self.publisher_layout)

    def post_build(self):
        super(QtPipelinePublishWidget, self).post_build()
        self.combo.currentIndexChanged.connect(self._on_publisher_changed)

    def _parse_publish(self, publish_plugins):
        publish_group_widget = QtWidgets.QGroupBox('publish')
        publish_layout = QtWidgets.QVBoxLayout()
        publish_group_widget.setLayout(publish_layout)
        for index, publish_plugin in enumerate(publish_plugins):
            publish_plugin.setdefault('options', {})
            widget_options = publish_plugin['_widget_obj'].extract_options()
            publish_plugin['options'].update(widget_options)

    def _build_publish(self, publish_plugins):
        publish_group_widget = QtWidgets.QGroupBox('publish')
        publish_layout = QtWidgets.QVBoxLayout()
        publish_group_widget.setLayout(publish_layout)
        for index, publish_plugin in enumerate(publish_plugins):
            publish_widget = self.fetch_widget(publish_plugin, 'publish')
            self.current['publish'][index]['_widget_obj'] = publish_widget
            publish_layout.addWidget(publish_widget)

        return publish_group_widget

    def _parse_context(self, context_plugins):
        publish_group_widget = QtWidgets.QGroupBox('context')
        publish_layout = QtWidgets.QVBoxLayout()
        publish_group_widget.setLayout(publish_layout)
        for index, context_plugin in enumerate(context_plugins):
            context_plugin.setdefault('options', {})
            widget_options = context_plugin['_widget_obj'].extract_options()
            context_plugin['options'].update(widget_options)

    def _build_context(self, context_plugins):
        context_group_widget = QtWidgets.QGroupBox('context')
        context_layout = QtWidgets.QVBoxLayout()
        context_group_widget.setLayout(context_layout)
        for index, context_plugin in enumerate(context_plugins):
            context_widget = self.fetch_widget(context_plugin, 'context')
            self.current['context'][index]['_widget_obj'] = context_widget
            context_layout.addWidget(context_widget)

        return context_group_widget

    def _parse_stages(self, component_stages):
        component_widget = QtWidgets.QWidget()
        component_layout = QtWidgets.QVBoxLayout()
        component_widget.setLayout(component_layout)

        for stage_name, stage_plugins in component_stages.items():
            stage_widget = QtWidgets.QGroupBox(stage_name)
            stage_layout = QtWidgets.QVBoxLayout()
            stage_widget.setLayout(stage_layout)
            component_layout.addWidget(stage_widget)

            for index, stage_plugin in enumerate(stage_plugins):
                stage_plugin.setdefault('options', {})
                widget_options = stage_plugin['_widget_obj'].extract_options()
                stage_plugin['options'].update(widget_options)

    def _build_stages(self, component_stages, component_name):
        component_widget = QtWidgets.QWidget()
        component_layout = QtWidgets.QVBoxLayout()
        component_widget.setLayout(component_layout)

        for stage_name, stage_plugins in component_stages.items():
            stage_widget = QtWidgets.QGroupBox(stage_name)
            stage_layout = QtWidgets.QVBoxLayout()
            stage_widget.setLayout(stage_layout)
            component_layout.addWidget(stage_widget)

            for index, stage_plugin in enumerate(stage_plugins):
                stage_widget = self.fetch_widget(stage_plugin, stage_name)
                self._current_publisher['components'][component_name][stage_name][index]['_widget_obj'] = stage_widget
                stage_layout.addWidget(stage_widget)

        return component_widget

    def on_publishers_loaded(self, event):
        for publisher in event['data']:
            for item_name, item in publisher.items():
                self.combo.addItem(item_name, item)

    def _on_publisher_changed(self, index):
        '''Slot triggered on asset type change.'''
        self.resetLayout(self.task_layout)
        self.build()

        package_publisher = self.combo.itemData(index)
        self._current_publisher = package_publisher

        contexts = package_publisher['context']
        components = package_publisher['components']
        publishers = package_publisher['publish']

        context_widget = self._build_context(contexts)
        self.context_layout.addWidget(context_widget)

        for component_name, component_stages in components.items():
            stages_widget = self._build_stages(component_stages, component_name)
            self.components_widget.addTab(stages_widget, component_name)

        publish_widget = self._build_publish(publishers)
        self.publisher_layout.addWidget(publish_widget)

    def extract(self):
        contexts = self.current['context']
        self._parse_context(contexts)
        components = self.current['components']
        for component_name, component_stages in components.items():
            self._parse_stages(component_stages)

        publishers = self.current['publish']
        self._parse_publish(publishers)

    def _sanitize_for_host(self, publisher_package):
        if '_widget_obj' in publisher_package:
            publisher_package.pop('_widget_obj')

        for key, value in publisher_package.items():
            if isinstance(value, list):
                for item in value:
                    self._sanitize_for_host(item)

            elif isinstance(value, dict):

                self._sanitize_for_host(value)

    def _on_run(self):
        self.extract()
        self._sanitize_for_host(self.current)
        from pprint import pformat
        self.logger.info(pformat(self.current))


if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    wid = QtPipelinePublishWidget(ui=constants.UI, host=constants.HOST)
    wid.show()
    sys.exit(app.exec_())
