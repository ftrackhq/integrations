#! /usr/bin/env python

import ftrack_api
import sys
import itertools
from QtExt import QtWidgets, QtGui, QtCore
from ftrack_connect_pipeline import get_registered_assets, register_assets
from ftrack_connect_pipeline import constants
from ftrack_connect_pipeline.ui.base.publish import BasePublishUiFramework
from ftrack_connect.ui.widget import header


import logging
logger = logging.getLogger(__name__)


def merge_list(list_data):
    logger.info('Merging {} '.format(list_data))
    result = list(set(itertools.chain.from_iterable(list_data)))
    logger.info('into {}'.format(result))
    return result


def merge_dict(dict_data):
    logger.info('Merging {} '.format(dict_data))
    result =  {k: v for d in dict_data for k, v in d.items()}
    logger.info('into {}'.format(result))
    return result


class NewApiEventHubThread(QtCore.QThread):
    '''Listen for events from ftrack's event hub.'''

    def start(self, session):
        '''Start thread for *session*.'''
        self._session = session
        super(NewApiEventHubThread, self).start()

    def run(self):
        '''Listen for events.'''
        self._session.event_hub.wait()


class QtFrameworkPublishWidget(BasePublishUiFramework, QtWidgets.QWidget):
    stage_start = QtCore.Signal(object)
    stage_done = QtCore.Signal(object)

    widget_suffix = 'widget.qt'

    def _on_stage_start(self, event_task_name):
        logger.debug('Starting stage: {}'.format(event_task_name))
        fn = self.mapping[event_task_name][1]
        widgets = self.__widget_stack[event_task_name]
        fn(widgets)

    def _on_stage_done(self, event_task_name):
        logger.debug('stage: {} done'.format(event_task_name))
        current_stage = constants.PUBLISH_ORDER.index(event_task_name)

        next_stage_idx = current_stage+1

        if next_stage_idx >= len(constants.PUBLISH_ORDER):
            # we reached the end, no more steps to perform !
            return

        next_stage = constants.PUBLISH_ORDER[current_stage+1]
        self.stage_start.emit(next_stage)

    def on_handle_async_reply(self, event):
        event_data = event['data']
        event_task_name = event_data.keys()[0]
        event_task_value = event_data.values()[0]

        logger.debug(
            'setting result for task: {} as {}'.format(
                event_task_name, event_task_value
            )
        )
        self._task_results[event_task_name] = event_task_value
        self.stage_done.emit(event_task_name)

    def run_async(self, event_list):
        logger.debug(
            'Sending event list {} to host'.format(event_list)
        )

        self.session.event_hub.publish(
            ftrack_api.event.base.Event(
                topic=constants.PIPELINE_RUN_TOPIC,
                data={'event_list': event_list}
            ),
            on_reply=self.on_handle_async_reply
        )

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
        collected_data = merge_list(self._task_results[constants.COLLECTORS])
        context_data = merge_dict(self._task_results[constants.CONTEXT])

        logger.debug('collected data:{}'.format(collected_data))
        logger.debug('context data:{}'.format(context_data))

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
        collected_data = merge_list(self._task_results[constants.COLLECTORS])
        context_data = merge_dict(self._task_results[constants.CONTEXT])
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
        context_data = merge_dict(self._task_results[constants.CONTEXT])
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

    def __init__(self, host=None, parent=None):
        super(QtFrameworkPublishWidget, self).__init__(parent=None)
        self.setWindowTitle('Standalone Pipeline Publisher')

        self.__widget_stack = {}
        self._task_results = {}

        self._event_thread = NewApiEventHubThread()
        self._event_thread.start(self.session)

        register_assets(self.session)
        self._asset_configs = get_registered_assets('Task')

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
        self.stage_done.connect(self._on_stage_done)
        self.stage_start.connect(self._on_stage_start)

    def _on_run(self):
        for stage in constants.PUBLISH_ORDER:
            self._task_results.setdefault(stage, [])

        self.stage_start.emit('context')

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
