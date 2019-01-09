#! /usr/bin/env python

import sys

import ftrack_api

from QtExt import QtWidgets, QtGui, QtCore

from ftrack_connect_pipeline import constants
from ftrack_connect_pipeline.ui.base.publish import BasePublishUiFramework
from ftrack_connect_pipeline.ui.qt import QtFrameworkBaseWidget, utils

from ftrack_connect.ui.widget import header


class QtFrameworkPublishWidget(BasePublishUiFramework, QtFrameworkBaseWidget):
    widget_suffix = 'widget.qt'

    def __init__(self, host=None, parent=None):
        super(QtFrameworkPublishWidget, self).__init__(parent=None)
        self.setWindowTitle('Standalone Pipeline Publisher')

        self.__widget_stack = {}

        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)

        self.header = header.Header(self.session.api_user)
        self.layout().addWidget(self.header)

        self.combo = QtWidgets.QComboBox()
        self.combo.addItem('- Select asset type -')
        self.layout().addWidget(self.combo)
        self.combo.currentIndexChanged.connect(self._on_asset_change)
        self.task_layout = QtWidgets.QVBoxLayout()
        self.layout().addLayout(self.task_layout)

        self.build()

        button = QtWidgets.QPushButton('Run')
        button.clicked.connect(self._on_run)
        self.layout().addWidget(button)

    def _on_run_context(self, widgets):
        event_list = []
        for widget in widgets:
            options = widget.extract_options()
            topic = widget.call_topic

            event_list.append(
                {
                    'topic': topic,
                    'options': options,
                    'type': constants.CONTEXT
                }
            )

        self.run_async(event_list)

    def _on_run_collectors(self, widgets):
        event_list = []

        for widget in widgets:
            options = widget.extract_options()
            topic = widget.call_topic

            event_list.append(
                {
                    'topic': topic,
                    'options': options,
                    'type': constants.COLLECTORS
                }
            )

        self.run_async(event_list)

    def _on_run_validators(self, widgets):
        collected_data = self.merge_list(self._task_results[constants.COLLECTORS])
        context_data = self.merge_dict(self._task_results[constants.CONTEXT])

        self.logger.debug('collected data:{}'.format(collected_data))
        self.logger.debug('context data:{}'.format(context_data))

        event_list = []

        # TODO: validate context data

        for widget in widgets:
            options = widget.extract_options()
            topic = widget.call_topic
            options.update(context_data)
            event_list.append(
                {
                    'topic': topic,
                    'options': options,
                    'data': collected_data,
                    'type': constants.VALIDATORS
                }
            )
        self.run_async(event_list)

    def _on_run_extractors(self, widgets):
        collected_data = self.merge_list(self._task_results[constants.COLLECTORS])
        context_data = self.merge_dict(self._task_results[constants.CONTEXT])
        validators_data = self._task_results[constants.VALIDATORS]

        if not all(validators_data):
            return

        event_list = []

        # TODO: validate context data

        for widget in widgets:
            options = widget.extract_options()
            topic = widget.call_topic
            options.update(context_data)
            event_list.append(
                {
                    'topic': topic,
                    'options': options,
                    'data': collected_data,
                    'type': constants.EXTRACTORS
                }
            )
        self.run_async(event_list)

    def _on_run_publishers(self, widgets):

        extracted_data = self._task_results[constants.EXTRACTORS]
        context_data = self.merge_dict(self._task_results[constants.CONTEXT])
        validators_data = self._task_results[constants.VALIDATORS]

        if not all(validators_data):
            return

        event_list = []

        # TODO: validate context data

        for widget in widgets:
            options = widget.extract_options()
            topic = widget.call_topic
            options.update(context_data)
            event_list.append(
                {
                    'topic': topic,
                    'options': options,
                    'data': extracted_data,
                    'type': constants.PUBLISHERS
                }
            )
        self.run_async(event_list)

    def clearLayout(self, layout):
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
                else:
                    self.clearLayout(item.layout())

    def _on_asset_change(self, index):
        self.clearLayout(self.task_layout)

        asset_name = self.combo.itemData(index)
        asset_schema = self._asset_configs.get(asset_name)
        if not asset_schema:
            return

        publish_stages = asset_schema[constants.PUBLISH]['plugins']
        for publish_stage in publish_stages:
            for publish_stage, publish_plugins in publish_stage.items():

                base_topic = self.mapping[publish_stage][0]

                box = QtWidgets.QGroupBox(publish_stage)
                plugin_layout = QtWidgets.QVBoxLayout()
                box.setLayout(plugin_layout)

                self.__widget_stack.setdefault(publish_stage, [])

                for plugin in publish_plugins:
                    widget = self.fetch_widget(plugin, base_topic, publish_stage)
                    if widget:
                        widget_is_visible = plugin.get('visible', True)
                        if not widget_is_visible:
                            widget.setVisible(False)

                        plugin_layout.addWidget(widget)
                        self.__widget_stack[publish_stage].append(widget)

                self.task_layout.addWidget(box)

    def build(self):
        for asset_name in self._asset_configs.keys():
            self.combo.addItem(asset_name, asset_name)



if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    wid = QtFrameworkPublishWidget()
    wid.show()
    sys.exit(app.exec_())
