import ftrack_api

from QtExt import QtWidgets, QtGui, QtCore

from ftrack_connect_pipeline import constants
from ftrack_connect_pipeline.qt import utils
from ftrack_connect_pipeline.base import BaseUiPipeline

from ftrack_connect.ui.widget import header


class BaseQtPipelineWidget(BaseUiPipeline, QtWidgets.QWidget):
    widget_suffix = 'widget.qt'

    stage_start = QtCore.Signal()
    stage_done = QtCore.Signal()

    def __init__(self, parent=None):
        super(BaseQtPipelineWidget, self).__init__(parent=parent)
        self._iteractive = False
        layout = QtWidgets.QVBoxLayout()

        self.setLayout(layout)
        self.header = header.Header(self.session.api_user)
        self.layout().addWidget(self.header)

        self.__widget_stack = {}
        self.reset_stages()

        self.combo = QtWidgets.QComboBox()
        self.combo.addItem('- Select asset type -')
        self.layout().addWidget(self.combo)
        self.task_layout = QtWidgets.QVBoxLayout()
        self.layout().addLayout(self.task_layout)

        self.build()

        self.combo.currentIndexChanged.connect(self._on_asset_change)

        button = QtWidgets.QPushButton('Run')
        button.clicked.connect(self._on_run)
        self.layout().addWidget(button)

        self._event_thread = utils.NewApiEventHubThread()
        self._event_thread.start(self.session)

        self.stage_done.connect(self._on_stage_done)
        self.stage_start.connect(self._on_stage_start)

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

        self._current_asset_type = asset_schema['asset_type']

        stages = asset_schema[self.stage_type]['plugins']
        for stage in stages:
            for current_stage, current_plugins in stage.items():
                base_topic = self.mapping[current_stage][0]

                box = QtWidgets.QGroupBox(current_stage)
                plugin_layout = QtWidgets.QVBoxLayout()
                box.setLayout(plugin_layout)

                self.__widget_stack.setdefault(current_stage, [])

                for plugin in current_plugins:
                    widget = self.fetch_widget(plugin, base_topic, current_stage)
                    if widget:
                        widget_is_visible = plugin.get('visible', True)
                        if not widget_is_visible:
                            widget.setVisible(False)

                        plugin_layout.addWidget(widget)
                        self.__widget_stack[current_stage].append(widget)

                self.task_layout.addWidget(box)

    def build(self):
        for asset_name in self._asset_configs.keys():
            asset_type = self._asset_configs[asset_name]['asset_type']
            self.combo.addItem('{} ({})'.format(asset_name, asset_type), asset_name)

    # event handling
    def on_handle_async_reply(self, event):
        event_data = event['data']
        event_task_name = event_data.keys()[0]
        event_task_value = event_data.values()[0]

        self.logger.debug(
            'setting result for task: {} as {}'.format(
                event_task_name, event_task_value
            )
        )
        self._stages_results[event_task_name] = event_task_value

        if not self._iteractive:
            # automatically process next stage
            self.stage_done.emit()

    def run_async(self, event_list):
        self.logger.debug(
            'Sending event list {} to host'.format(event_list)
        )

        self.session.event_hub.publish(
            ftrack_api.event.base.Event(
                topic=constants.PIPELINE_RUN_TOPIC,
                data={'event_list': event_list}
            ),
            on_reply=self.on_handle_async_reply
        )

    # widget handling
    def fetch_widget(self, plugin, base_topic, plugin_type):
        ui = plugin.get('plugin_ui', 'default.{}'.format(self.widget_suffix))
        mytopic = base_topic.format(ui)

        # filter widgets which cannot be loaded in this host.
        if self.widget_suffix not in mytopic:
            self.logger.warning('cannot load widget topic of type {} for {}'.format(
                mytopic, self.widget_suffix
            ))
            return

        plugin_options = plugin.get('options', {})
        plugin_name = plugin.get('name', 'no name provided')
        description = plugin.get('description', 'No description provided')
        plugin_topic = self.mapping[plugin_type][0].format(plugin['plugin'])

        result_widget = self.session.event_hub.publish(
            ftrack_api.event.base.Event(
                topic=mytopic,
                data={
                    'options': plugin_options,
                    'name': plugin_name,
                    'description': description,
                    'plugin_topic': plugin_topic
                }
            ),
            synchronous=True
        )
        self.logger.info('UI WIDGET : {} FOUND: {}'.format(mytopic, result_widget))
        if result_widget:
            return result_widget[0]

    # Stage management
    def _on_run(self):
        self.process_stages()

    def _on_stage_start(self, ):
        self.logger.debug('Starting stage: {}'.format(self.current_stage))
        fn = self.mapping[self.current_stage][1]
        widgets = self.__widget_stack[self.current_stage]
        fn(widgets)

    def _on_stage_done(self):
        self.logger.debug('stage: {} done'.format(self.current_stage))
        if not self.next_stage:
            self.reset_stages()
            return

        self.current_stage = self.next_stage
        self.stage_start.emit()

    def process_stages(self):
        for stage in self.mapping.keys():
            self._stages_results.setdefault(stage, [])

        self.stage_start.emit()

    def reset_stages(self):
        self._current_stage = None

    @property
    def previous_stage(self):
        self.logger.info('current_stage :{}'.format(self.current_stage))
        current_stage_idx = self.mapping.keys().index(self.current_stage)

        previous_stage_idx = current_stage_idx - 1

        if previous_stage_idx < 0:
            # we reached the end, no more steps to perform !
            return

        previous_stage = self.mapping.keys()[previous_stage_idx]
        self.logger.info('previous_stage :{}'.format(previous_stage))
        return previous_stage

    @property
    def next_stage(self):
        self.logger.info('current_stage :{}'.format(self.current_stage))
        current_stage_idx = self.mapping.keys().index(self.current_stage)

        next_stage_idx = current_stage_idx + 1

        if next_stage_idx >= len(self.mapping.keys()):
            # we reached the end, no more steps to perform !
            return

        next_stage = self.mapping.keys()[next_stage_idx]
        self.logger.info('next_stage :{}'.format(next_stage))
        return next_stage

    @property
    def current_stage(self):
        return self._current_stage or self.mapping.keys()[0]

    @current_stage.setter
    def current_stage(self, stage):
        if stage not in self.mapping.keys():
            self.logger.warning('Stage {} not in {}'.format(stage, self.mapping.keys()))
            return

        self._current_stage = stage