#! /usr/bin/env python
# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import os
import sys

deps_paths = os.environ.get('PYTHONPATH', '').split(os.pathsep)
for path in deps_paths:
    sys.path.append(path)


from collections import OrderedDict

from QtExt import QtGui
from ftrack_connect_pipeline import constants
from ftrack_connect_pipeline import utils
from ftrack_connect_pipeline.qt import BaseQtPipelineWidget


class QtPipelineLoaderWidget(BaseQtPipelineWidget):

    def __init__(self, ui, host, parent=None):
        stage_type = constants.LOAD
        stages_mapping = OrderedDict([
            (constants.CONTEXT,   self.run_context),
            (constants.IMPORTERS, self.run_importers)
        ])
        super(QtPipelineLoaderWidget, self).__init__(stage_type, stages_mapping, ui, host, parent=parent)
        self.setWindowTitle('Standalone Pipeline Loader')

    def run_context(self):
        '''Run context stage'''
        data = self.stages_manager.widgets.get(self.stages_manager.current_stage, [])
        event_list = []
        for (widget, plugin) in data:
            context = widget.extract_options()

            event_list.append(
                {
                    'settings': {
                        'context': context,
                        'data': None,
                        'options': None
                    },
                    'pipeline': {
                        'plugin_name': plugin['plugin'],
                        'plugin_type': constants.CONTEXT,
                        'type': 'plugin',
                        'host': self.host,
                    },
                }
            )

        self.stages_manager.run_async(event_list)

    def run_importers(self):
        '''Run importers stage'''

        component_data = utils.merge_dict(self.stages_manager.results[constants.CONTEXT])

        data = self.stages_manager.widgets.get(self.stages_manager.current_stage, [])
        event_list = []
        for (widget, plugin) in data:
            options = widget.extract_options()

            event_list.append(
                {
                    'settings': {
                        'context':None,
                        'data': component_data,
                        'options': options
                    },
                    'pipeline': {
                        'plugin_name': plugin['plugin'],
                        'plugin_type': constants.IMPORTERS,
                        'type': 'plugin',
                        'host': self.host,
                    },
                }
            )

        self.stages_manager.run_async(event_list)


if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    wid = QtPipelineLoaderWidget(ui=constants.UI, host=constants.HOST)
    wid.show()
    sys.exit(app.exec_())
