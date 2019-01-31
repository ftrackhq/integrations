import ftrack_api
import logging

from QtExt import QtWidgets, QtGui, QtCore

from ftrack_connect_pipeline.qt import utils as qtutils
from ftrack_connect_pipeline import utils

from ftrack_connect.ui.widget import header
from ftrack_connect.ui import theme


class BaseQtPipelineWidget(QtWidgets.QWidget):
    widget_suffix = 'widget.qt'

    @property
    def asset_type(self):
        '''Return current asset type'''
        return self._current_asset_type

    def __init__(self, stage_type, stages_mapping, parent=None):
        '''Initialise widget with *stage_type* and *stage_mapping*.'''
        super(BaseQtPipelineWidget, self).__init__(parent=parent)

        self._current_asset_type = None

        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )

        self.session = ftrack_api.Session(auto_connect_event_hub=True)
        self.stages_manager = qtutils.StageManager(
            self.session, stages_mapping, stage_type
        )

        context_type = 'Task'
        self.assets_manager = utils.AssetSchemaManager(self.session, context_type)

        self.build()
        self.post_build()

        theme.applyFont()
        # theme.applyTheme(self, 'dark', 'cleanlooks')

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
        self.stages_manager.reset_stages()
        self.stages_manager.widgets.clear()

    def _on_asset_type_change(self, index):
        '''Slot triggered on asset type change.'''
        self.resetLayout(self.task_layout)

        asset_name = self.combo.itemData(index)
        asset_schema = self.assets_manager.assets.get(asset_name)
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

                base_topic = base_topic[0]

                box = QtWidgets.QGroupBox(current_stage)
                plugin_layout = QtWidgets.QVBoxLayout()
                box.setLayout(plugin_layout)

                self.stages_manager.widgets.setdefault(current_stage, [])

                for plugin in current_plugins:
                    widget = self.fetch_widget(plugin, base_topic, current_stage)
                    if widget:
                        widget_is_visible = plugin.get('visible', True)
                        if not widget_is_visible:
                            widget.setVisible(False)

                        plugin_layout.addWidget(widget)
                        self.stages_manager.widgets[current_stage].append(widget)

                self.task_layout.addWidget(box)

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

        for asset_name in self.assets_manager.assets.keys():
            asset_type = self.assets_manager.assets[asset_name]['asset_type']
            self.combo.addItem('{} ({})'.format(asset_name, asset_type), asset_name)

        self.run_button = QtWidgets.QPushButton('Run')
        self.layout().addWidget(self.run_button)

    def post_build(self):
        '''Post Build ui method.'''
        self.run_button.clicked.connect(self._on_run)
        self.combo.currentIndexChanged.connect(self._on_asset_type_change)

        self.stages_manager.stage_error.connect(self._on_stage_error)
        self.stages_manager.stages_end.connect(self._on_stages_end)

        self._event_thread = qtutils.NewApiEventHubThread()
        self._event_thread.start(self.session)

    def _on_stage_error(self, error):
        self.header.setMessage(error, level='error')

    def _on_stages_end(self):
        self.header.setMessage('DONE!', level='info')

    # widget handling
    def fetch_widget(self, plugin, base_topic, plugin_type):
        '''Fetch widgets defined in the asset schema.'''
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
        plugin_topic = self.stages_manager.stages[plugin_type][0].format(plugin['plugin'])

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
        self.logger.debug('widget found {} for {}'.format(result_widget, mytopic))
        if result_widget:
            return result_widget[0]

    # Stage management
    def _on_run(self):
        '''Slot triggered with run button.'''
        # start processing the stages.
        self.stages_manager.reset_stages()
        self.stages_manager.process_stages()
