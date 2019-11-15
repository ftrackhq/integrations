#! /usr/bin/env python
# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import sys
import os

deps_paths = os.environ.get('PYTHONPATH', '').split(os.pathsep)
for path in deps_paths:
    sys.path.append(path)

from Qt import QtWidgets

from ftrack_connect_pipeline import constants
from ftrack_connect_pipeline.client import BaseQtPipelineWidget


class QtPipelinePublishWidget(BaseQtPipelineWidget):

    def __init__(self, ui, host, hostid=None, parent=None):
        super(QtPipelinePublishWidget, self).__init__(ui, host, hostid, parent=parent)
        self.setWindowTitle('Standalone Pipeline Publisher')
        self.fetch_publisher_definitions()

    def build(self):
        '''build widgets.'''
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
        '''connect widget events'''
        super(QtPipelinePublishWidget, self).post_build()
        self.combo.currentIndexChanged.connect(self._on_publisher_changed)
        # reset the definitions compboxbox
        self.hostid_changed.connect(self.combo.clear)
        # fetch new defintions
        self.hostid_changed.connect(self.fetch_publisher_definitions)
        self.hostid_changed.connect(self.fetch_package_definitions)

    def fetch_publisher_definitions(self):
        '''fetch the publishers definitions.'''
        self._fetch_defintions("publisher", self._publishers_loaded)

    def _publishers_loaded(self, event):
        '''event callback for when the publishers are loaded.'''
        raw_data = event['data']

        for item_name, item in raw_data.items():
            self.combo.addItem(item_name, item)

    # build widgets functions
    def _build_widgets(self, package_publisher):
        '''build all the widgets defined by the *package_publisher*'''
        if not package_publisher:
            return

        contexts = package_publisher[constants.CONTEXT]
        components = package_publisher[constants.COMPONENTS]
        publishers = package_publisher[constants.PUBLISH]

        context_widget = self._build_context(contexts)
        self.context_layout.addWidget(context_widget)

        for component_name, component_stages in components.items():
            stages_widget = self._build_stages(component_stages)
            self.components_widget.addTab(stages_widget, component_name)

        publish_widget = self._build_publish(publishers)
        self.publisher_layout.addWidget(publish_widget)

    def _build_context(self, context_plugins):
        context_group_widget = QtWidgets.QGroupBox(constants.CONTEXT)
        context_layout = QtWidgets.QVBoxLayout()
        context_group_widget.setLayout(context_layout)

        extra_options = {
            'context_id': self.context['id'],
            'asset_type': self.packages[self.schema['package']]['type']
        }

        for context_plugin in context_plugins:
            context_widget = self.fetch_widget(
                context_plugin, constants.CONTEXT,
                extra_options
            )
            self.register_widget_plugin(context_widget, context_plugin)
            context_layout.addWidget(context_widget)

        return context_group_widget

    def _build_stages(self, component_stages):
        component_widget = QtWidgets.QWidget()
        component_layout = QtWidgets.QVBoxLayout()
        component_widget.setLayout(component_layout)

        for stage_name, stage_plugins in component_stages.items():
            stage_widget = QtWidgets.QGroupBox(stage_name)
            stage_layout = QtWidgets.QVBoxLayout()
            stage_widget.setLayout(stage_layout)
            component_layout.addWidget(stage_widget)

            for stage_plugin in stage_plugins:
                stage_widget = self.fetch_widget(stage_plugin, stage_name)
                self.register_widget_plugin(stage_widget, stage_plugin)
                stage_layout.addWidget(stage_widget)

        return component_widget

    def _build_publish(self, publish_plugins):
        publish_group_widget = QtWidgets.QGroupBox(constants.PUBLISH)
        publish_layout = QtWidgets.QVBoxLayout()
        publish_group_widget.setLayout(publish_layout)
        for publish_plugin in publish_plugins:
            publish_widget = self.fetch_widget(publish_plugin, constants.PUBLISH)
            self.register_widget_plugin(publish_widget, publish_plugin)
            publish_layout.addWidget(publish_widget)

        return publish_group_widget

    # parse widgets results functions
    def _parse_publish(self, publish_plugins):
        publish_group_widget = QtWidgets.QGroupBox(constants.PUBLISH)
        publish_layout = QtWidgets.QVBoxLayout()
        publish_group_widget.setLayout(publish_layout)
        for publish_plugin in publish_plugins:
            widget = self.get_registered_widget_plugin(publish_plugin)
            widget_options = widget.get_option_results()
            publish_plugin.setdefault('options', {})
            publish_plugin['options'].update(widget_options)

    def _parse_context(self, context_plugins):
        publish_group_widget = QtWidgets.QGroupBox(constants.CONTEXT)
        publish_layout = QtWidgets.QVBoxLayout()
        publish_group_widget.setLayout(publish_layout)
        for context_plugin in context_plugins:
            widget = self.get_registered_widget_plugin(context_plugin)
            widget_options = widget.get_option_results()
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

            for stage_plugin in stage_plugins:
                widget = self.get_registered_widget_plugin(stage_plugin)
                widget_options = widget.get_option_results()
                stage_plugin.setdefault('options', {})
                stage_plugin['options'].update(widget_options)

    def _on_publisher_changed(self, index):
        '''Slot triggered on asset type change.'''
        self.resetLayout(self.task_layout)
        self.build()

        package_publisher = self.combo.itemData(index)
        self._current = package_publisher
        self._build_widgets(package_publisher)

    def _update_publish_data(self):
        '''ensure the stored data are updated with the latest value'''
        contexts = self.schema[constants.CONTEXT]
        self._parse_context(contexts)
        components = self.schema[constants.COMPONENTS]
        for component_name, component_stages in components.items():
            self._parse_stages(component_stages)

        publishers = self.schema[constants.PUBLISH]
        self._parse_publish(publishers)

    def _on_run(self):
        super(QtPipelinePublishWidget, self)._on_run()
        self._update_publish_data()
        self.send_to_host(self.schema, constants.PIPELINE_RUN_HOST_PUBLISHER)


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    wid = QtPipelinePublishWidget(ui=constants.UI, host=constants.HOST)
    wid.show()
    sys.exit(app.exec_())
