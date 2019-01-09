from QtExt import QtWidgets, QtGui, QtCore

from ftrack_connect_pipeline.ui.qt import utils
from ftrack_connect_pipeline.ui.base import BaseUiFramework


class QtFrameworkBaseWidget(BaseUiFramework, QtWidgets.QWidget):

    stage_start = QtCore.Signal(object)
    stage_done = QtCore.Signal(object)

    def __init__(self, parent=None):
        super(QtFrameworkBaseWidget, self).__init__(parent=parent)
        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)

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