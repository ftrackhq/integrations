# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import os

import ftrack_api
import logging

from QtExt import QtWidgets

from ftrack_connect_pipeline.client import utils as qtutils
from ftrack_connect_pipeline import event
from ftrack_connect_pipeline.session import get_shared_session
from ftrack_connect_pipeline import constants
from ftrack_connect.ui.widget import header
from ftrack_connect.ui import theme


class BaseQtPipelineWidget(QtWidgets.QWidget):

    @property
    def host(self):
        return self._host

    @property
    def ui(self):
        return self._ui

    def __init__(self, ui, host, parent=None):
        '''Initialise widget with *stage_type* and *stage_mapping*.'''
        super(BaseQtPipelineWidget, self).__init__(parent=parent)

        self._ui = ui
        self._host = host

        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )

        self.session = get_shared_session()
        self.event_manager = event.EventManager(self.session, True)

        self.build()
        self.post_build()

        theme.applyFont()

    def resetLayout(self, layout):
        '''Reset layout and delete widgets.'''
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
                else:
                    self.resetLayout(item.layout())
        # self.stages_manager.reset_stages()
        # self.stages_manager.widgets.clear()
    #
    # def _on_package_type_change(self, index):
    #     '''Slot triggered on asset type change.'''
    #     self.resetLayout(self.task_layout)
    #
    #     asset_name = self.combo.itemData(index)
    #     asset_schema = self.package_manager.package.get(asset_name)
    #     if not asset_schema:
    #         return
    #
    #     self._current_asset_type = asset_schema['asset_type']
    #
    #     stages = asset_schema[self.stages_manager.type]['plugins']
    #     for stage in stages:
    #         for current_stage, current_plugins in stage.items():
    #             base_topic = self.stages_manager.stages.get(current_stage)
    #             if not base_topic:
    #                 self.logger.warning(
    #                     'stage {} cannot be evaluated'.format(current_stage))
    #                 continue
    #
    #             box = QtWidgets.QGroupBox(current_stage)
    #             plugin_layout = QtWidgets.QVBoxLayout()
    #             box.setLayout(plugin_layout)
    #
    #             self.stages_manager.widgets.setdefault(current_stage, [])
    #
    #             for plugin in current_plugins:
    #                 widget = self.fetch_widget(plugin, current_stage)
    #                 if widget:
    #                     widget_is_visible = plugin.get('visible', True)
    #                     if not widget_is_visible:
    #                         widget.setVisible(False)
    #
    #                     plugin_layout.addWidget(widget)
    #                     self.stages_manager.widgets[current_stage].append(
    #                         (widget, plugin)
    #                     )
    #
    #             self.task_layout.addWidget(box)

    def build(self):
        '''Build ui method.'''
        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)
        self.header = header.Header(self.session.api_user)
        self.layout().addWidget(self.header)
        self.combo = QtWidgets.QComboBox()
        self.combo.addItem('- Select asset type -')
        self.layout().addWidget(self.combo)
        self.task_layout = QtWidgets.QVBoxLayout()
        self.layout().addLayout(self.task_layout)

        # for asset_name in self.package_manager.package.keys():
        #     asset_type = self.package_manager.package[asset_name]['asset_type']
        #     self.combo.addItem('{} ({})'.format(asset_name, asset_type),
        #                        asset_name)

        self.run_button = QtWidgets.QPushButton('Run')
        self.layout().addWidget(self.run_button)

    def post_build(self):
        '''Post Build ui method.'''
        self.run_button.clicked.connect(self._on_run)
        # self.combo.currentIndexChanged.connect(self._on_package_type_change)

        # self.stages_manager.stage_error.connect(self._on_stage_error)
        # self.stages_manager.stages_end.connect(self._on_stages_end)

    def _on_stage_error(self, error):
        self.header.setMessage(error, level='error')

    def _on_stages_end(self):
        self.header.setMessage('DONE!', level='info')

    # widget handling
    def fetch_widget(self, plugin, plugin_type):
        '''Fetch widgets defined in the asset schema.'''
        ui = plugin.get('widget', 'default.widget')

        plugin_options = plugin.get('options', {})
        plugin_name = plugin.get('name', 'no name provided')
        description = plugin.get('description', 'No description provided')

        event = ftrack_api.event.base.Event(
            topic=constants.PIPELINE_REGISTER_TOPIC,
            data={
                'pipeline': {
                    'plugin_name': ui,
                    'plugin_type': plugin_type,
                    'type': 'widget',
                    'ui': self.ui,
                    'host': self.host,
                },
                'settings':
                    {
                        'options': plugin_options,
                        'name': plugin_name,
                        'description': description,
                    }
            }
        )

        self.logger.info('publishing event: {}'.format(event))

        result_widget = self.session.event_hub.publish(
            event,
            synchronous=True
        )

        if result_widget:
            return result_widget[0]

    # Stage management
    def _on_run(self):
        '''Slot triggered with run button.'''
        # start processing the stages.
        # self.stages_manager.reset_stages()
        self.stages_manager.process_stages()
