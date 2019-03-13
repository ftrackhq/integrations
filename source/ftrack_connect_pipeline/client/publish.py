#! /usr/bin/env python
# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import sys
import os

deps_paths = os.environ.get('PYTHONPATH', '').split(os.pathsep)
for path in deps_paths:
    sys.path.append(path)

from QtExt import QtGui, QtWidgets

from ftrack_connect_pipeline.host import utils
from ftrack_connect_pipeline import constants
from ftrack_connect_pipeline.client import BaseQtPipelineWidget


class QtPipelinePublishWidget(BaseQtPipelineWidget):

    def __init__(self, ui, host, parent=None):
        super(QtPipelinePublishWidget, self).__init__(ui, host, parent=parent)
        self.setWindowTitle('Standalone Pipeline Publisher')

    def _on_publisher_change(self, index):
        '''Slot triggered on asset type change.'''
        self.resetLayout(self.task_layout)

        asset_name = self.combo.itemData(index)
        asset_schema = self.package_manager.package.get(asset_name)
        if not asset_schema:
            return

        self._current_asset_type = asset_schema['asset_type']

        stages = asset_schema[self.stages_manager.type]['plugins']
        for stage in stages:
            for current_stage, current_plugins in stage.items():
                base_topic = self.stages_manager.stages.get(current_stage)
                if not base_topic:
                    self.logger.warning('stage {} cannot be evaluated'.format(current_stage))
                    continue

                box = QtWidgets.QGroupBox(current_stage)
                plugin_layout = QtWidgets.QVBoxLayout()
                box.setLayout(plugin_layout)

                self.stages_manager.widgets.setdefault(current_stage, [])

                for plugin in current_plugins:
                    widget = self.fetch_widget(plugin, current_stage)
                    if widget:
                        widget_is_visible = plugin.get('visible', True)
                        if not widget_is_visible:
                            widget.setVisible(False)

                        plugin_layout.addWidget(widget)
                        self.stages_manager.widgets[current_stage].append(
                            (widget, plugin)
                        )

                self.task_layout.addWidget(box)


if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    wid = QtPipelinePublishWidget(ui=constants.UI, host=constants.HOST)
    wid.show()
    sys.exit(app.exec_())
