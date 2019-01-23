#! /usr/bin/env python

import sys
from collections import OrderedDict

from QtExt import QtWidgets, QtGui, QtCore
from ftrack_connect_pipeline import constants
from ftrack_connect_pipeline import utils
from ftrack_connect_pipeline.qt import BaseQtPipelineWidget



class QtPipelineLoaderWidget(BaseQtPipelineWidget):

    def __init__(self, host=None, parent=None):
        super(QtPipelineLoaderWidget, self).__init__(parent=None)
        self.setWindowTitle('Standalone Pipeline Loader')
        self.stage_type = constants.LOAD

        self.mapping = OrderedDict([
            (constants.CONTEXT,    (constants.CONTEXT_PLUGIN_TOPIC, self._on_run_context)),
            (constants.IMPORTERS,  (constants.IMPORTERS_PLUGIN_TOPIC, self._on_run_importers))
        ])

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

    def _on_run_importers(self, widgets):
        component_data = utils.merge_dict(self._stages_results[constants.CONTEXT])

        event_list = []
        for widget in widgets:
            options = widget.extract_options()
            topic = widget.plugin_topic
            options.update(component_data)

            event_list.append(
                {
                    'topic': topic,
                    'options': options,
                    'type': constants.IMPORTERS
                }
            )

        self.run_async(event_list)


if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    wid = QtPipelineLoaderWidget()
    wid.show()
    sys.exit(app.exec_())
