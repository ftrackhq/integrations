#! /usr/bin/env python
# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import os
import sys

deps_paths = os.environ.get('PYTHONPATH').split(os.pathsep)
for path in deps_paths:
    sys.path.append(path)


from collections import OrderedDict

from QtExt import QtGui

import inspect
import os
filename = inspect.getframeinfo(inspect.currentframe()).filename

PACKAGE_DIRECTORY = os.path.abspath(
    os.path.join(os.path.dirname(filename), '..', '..'))

sys.path.append(PACKAGE_DIRECTORY)

from ftrack_connect_pipeline import constants
from ftrack_connect_pipeline import utils
from ftrack_connect_pipeline.qt import BaseQtPipelineWidget


class QtPipelineLoaderWidget(BaseQtPipelineWidget):

    def __init__(self, parent=None):
        stage_type = constants.LOAD
        stages_mapping = OrderedDict([
            (constants.CONTEXT,    (constants.CONTEXT_PLUGIN_TOPIC, self.run_context)),
            (constants.IMPORTERS,  (constants.IMPORTERS_PLUGIN_TOPIC, self.run_importers))
        ])
        super(QtPipelineLoaderWidget, self).__init__(stage_type, stages_mapping, parent=parent)
        self.setWindowTitle('Standalone Pipeline Loader')

    def run_context(self):
        '''Run context stage'''
        widgets = self.stages_manager.widgets[self.stages_manager.current_stage]
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

        self.stages_manager.run_async(event_list)

    def run_importers(self):
        '''Run importers stage'''
        widgets = self.stages_manager.widgets[self.stages_manager.current_stage]
        component_data = utils.merge_dict(self.stages_manager.results[constants.CONTEXT])

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

        self.stages_manager.run_async(event_list)


if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    wid = QtPipelineLoaderWidget()
    wid.show()
    sys.exit(app.exec_())
