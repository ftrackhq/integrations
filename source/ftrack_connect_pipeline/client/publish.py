#! /usr/bin/env python
# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import sys
import os
import uuid
import copy
deps_paths = os.environ.get('PYTHONPATH', '').split(os.pathsep)
for path in deps_paths:
    sys.path.append(path)

from QtExt import QtGui, QtWidgets

import ftrack_api
from ftrack_connect_pipeline import constants
from ftrack_connect_pipeline.client import BaseQtPipelineWidget
from pprint import pformat


class QtPipelinePublishWidget(BaseQtPipelineWidget):

    @property
    def current(self):
        return self._current_publisher

    def __init__(self, ui, host, parent=None):
        super(QtPipelinePublishWidget, self).__init__(ui, host, parent=parent)
        self.setWindowTitle('Standalone Pipeline Publisher')

        self._current_publisher = {}

        publisher_event = ftrack_api.event.base.Event(
            topic=constants.PIPELINE_DEFINITION_TOPIC,
            data={
                'pipeline': {
                    'type': "publisher"
                }
            }
        )
        self.event_manager.publish(publisher_event, self.on_publishers_loaded)
        self._listen_widget_updates()

    def _update_widget(self, event):
        data = event['data']['data']
        widget_ref = event['data']['widget_ref']
        widget = self._widgets_ref.get(widget_ref)
        if not widget:
            self.logger.warning('Widget ref :{} not found ! '.format(widget_ref))
            return

        self.logger.info('updating widget: {} with {}'.format(widget, data))
        widget.setDisabled(True)

    def _listen_widget_updates(self):
        self.session.event_hub.subscribe(
            'topic={}'.format(constants.PIPELINE_UPDATE_UI),
            self._update_widget
        )


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

    def on_publishers_loaded(self, event):
        for publisher in event['data']:
            for item_name, item in publisher.items():
                self.combo.addItem(item_name, item)

    def build_widgets(self, package_publisher):

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

    def _build_context(self, context_plugins):
        context_group_widget = QtWidgets.QGroupBox('context')
        context_layout = QtWidgets.QVBoxLayout()
        context_group_widget.setLayout(context_layout)
        for index, context_plugin in enumerate(context_plugins):
            context_widget = self.fetch_widget(context_plugin, 'context')
            uid = uuid.uuid4().hex
            self.current['context'][index]['widget_ref'] = uid
            self._widgets_ref[uid] = context_widget
            context_layout.addWidget(context_widget)

        return context_group_widget

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
                uid = uuid.uuid4().hex

                self.current['components'][component_name][stage_name][index]['widget_ref'] = uid
                self._widgets_ref[uid] = stage_widget

                stage_layout.addWidget(stage_widget)

        return component_widget

    def _build_publish(self, publish_plugins):
        publish_group_widget = QtWidgets.QGroupBox('publish')
        publish_layout = QtWidgets.QVBoxLayout()
        publish_group_widget.setLayout(publish_layout)
        for index, publish_plugin in enumerate(publish_plugins):
            publish_widget = self.fetch_widget(publish_plugin, 'publish')
            uid = uuid.uuid4().hex
            self.current['publish'][index]['widget_ref'] = uid
            self._widgets_ref[uid] = publish_widget
            publish_layout.addWidget(publish_widget)

        return publish_group_widget

    def _parse_publish(self, publish_plugins):
        publish_group_widget = QtWidgets.QGroupBox('publish')
        publish_layout = QtWidgets.QVBoxLayout()
        publish_group_widget.setLayout(publish_layout)
        for index, publish_plugin in enumerate(publish_plugins):
            widget_options = self._widgets_ref[publish_plugin['widget_ref']].extract_options()
            publish_plugin.setdefault('options', {})
            publish_plugin['options'].update(widget_options)

    def _parse_context(self, context_plugins):
        publish_group_widget = QtWidgets.QGroupBox('context')
        publish_layout = QtWidgets.QVBoxLayout()
        publish_group_widget.setLayout(publish_layout)
        for index, context_plugin in enumerate(context_plugins):
            widget_options = self._widgets_ref[context_plugin['widget_ref']].extract_options()
            context_plugin.setdefault('options', {})
            context_plugin['options'].update(widget_options)

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
                widget_options = self._widgets_ref[stage_plugin['widget_ref']].extract_options()
                stage_plugin.setdefault('options', {})
                stage_plugin['options'].update(widget_options)

    def _on_publisher_changed(self, index):
        '''Slot triggered on asset type change.'''
        self.resetLayout(self.task_layout)
        self.build()

        package_publisher = self.combo.itemData(index)
        self._current_publisher = package_publisher
        self.build_widgets(package_publisher)

    def update_publish_data(self):
        contexts = self.current['context']
        self._parse_context(contexts)
        components = self.current['components']
        for component_name, component_stages in components.items():
            self._parse_stages(component_stages)

        publishers = self.current['publish']
        self._parse_publish(publishers)

    def _on_run(self):
        self.update_publish_data()
        self.send_to_host(self.current, constants.PIPELINE_RUN_PUBLISHER)


if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    wid = QtPipelinePublishWidget(ui=constants.UI, host=constants.HOST)
    wid.show()
    sys.exit(app.exec_())
