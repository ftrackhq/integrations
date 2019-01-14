#! /usr/bin/env python

import sys

from QtExt import QtWidgets, QtGui, QtCore

from ftrack_connect_pipeline import constants
from ftrack_connect_pipeline.ui.base.publish import BasePublishUiPipeline
from ftrack_connect_pipeline.ui.qt import BaseQtPipelineWidget



class QtPipelinePublishWidget(BasePublishUiPipeline, BaseQtPipelineWidget):

    def __init__(self, host=None, parent=None):
        super(QtPipelinePublishWidget, self).__init__(parent=None)
        self.setWindowTitle('Standalone Pipeline Publisher')
        self.stage_type = constants.PUBLISH

    def _on_run_context(self, widgets):
        event_list = []
        for widget in widgets:
            options = widget.extract_options()
            topic = widget.plugin_topic

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
            topic = widget.plugin_topic

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
            topic = widget.plugin_topic
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
            topic = widget.plugin_topic
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
            topic = widget.plugin_topic
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


if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    wid = QtPipelinePublishWidget()
    wid.show()
    sys.exit(app.exec_())
