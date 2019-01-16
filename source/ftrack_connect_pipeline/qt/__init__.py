from QtExt import QtWidgets, QtGui, QtCore

from ftrack_connect_pipeline.qt import utils
from ftrack_connect_pipeline.base import BaseUiPipeline

from ftrack_connect.ui.widget import header


class BaseQtPipelineWidget(BaseUiPipeline, QtWidgets.QWidget):
    widget_suffix = 'widget.qt'

    stage_start = QtCore.Signal(object)
    stage_done = QtCore.Signal(object)

    def __init__(self, parent=None):
        super(BaseQtPipelineWidget, self).__init__(parent=parent)
        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)
        self.header = header.Header(self.session.api_user)
        self.layout().addWidget(self.header)

        self.__widget_stack = {}

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

        self._event_thread = utils.NewApiEventHubThread()
        self._event_thread.start(self.session)

        self.stage_done.connect(self._on_stage_done)
        self.stage_start.connect(self._on_stage_start)

    def _on_run(self):
        for stage in self.stack_exec_order:
            self._task_results.setdefault(stage, [])

        self.stage_start.emit('context')

    def _on_stage_start(self, event_task_name):
        self.logger.debug('Starting stage: {}'.format(event_task_name))
        fn = self.mapping[event_task_name][1]
        widgets = self.__widget_stack[event_task_name]
        fn(widgets)

    def _on_stage_done(self, event_task_name):
        self.logger.debug('stage: {} done'.format(event_task_name))
        current_stage = self.stack_exec_order.index(event_task_name)

        next_stage_idx = current_stage+1

        if next_stage_idx >= len(self.stack_exec_order):
            # we reached the end, no more steps to perform !
            return

        next_stage = self.stack_exec_order[current_stage+1]
        self.stage_start.emit(next_stage)

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
            self.combo.addItem(asset_name, asset_name)
