# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from Qt import QtWidgets, QtCore, QtGui

from ftrack_framework_qt.widgets import BaseWidget

from ftrack_qt.widgets.selectors import PublishAssetSelector
from ftrack_qt.widgets.selectors import StatusSelector
from ftrack_qt.widgets.lines import LineWidget
from ftrack_qt.utils.decorators import invoke_in_qt_main_thread


class PublisherAssetVersionSelectorWidget(BaseWidget):
    '''Main class to represent a context widget on a publish process.'''

    name = 'publisher_asset_version_selector'
    ui_type = 'qt'

    def __init__(
        self,
        event_manager,
        client_id,
        context_id,
        plugin_config,
        group_config,
        on_set_plugin_option,
        on_run_ui_hook,
        parent=None,
    ):
        '''initialise PublishContextWidget with *parent*, *session*, *data*,
        *name*, *description*, *options* and *context*
        '''
        self._label = None
        self._asset_version_selector = None
        self._asset_status_label = None
        self._status_selector = None
        self._comments_input = None

        super(PublisherAssetVersionSelectorWidget, self).__init__(
            event_manager,
            client_id,
            context_id,
            plugin_config,
            group_config,
            on_set_plugin_option,
            on_run_ui_hook,
            parent,
        )

    def pre_build_ui(self):
        '''Set up the layout and size policy for the widget.'''
        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(QtCore.Qt.AlignTop)
        self.setLayout(layout)
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed
        )

    def build_ui(self):
        '''Build the UI elements for the widget.'''

        self._label = QtWidgets.QLabel()
        self._label.setObjectName('gray')
        self._label.setWordWrap(True)

        asset_layout = QtWidgets.QVBoxLayout()
        asset_layout.setAlignment(QtCore.Qt.AlignTop)

        # Create asset
        self._asset_version_selector = PublishAssetSelector()
        asset_layout.addWidget(self._asset_version_selector)
        self._asset_version_selector.set_default_new_asset_name(
            self.plugin_config['options'].get('asset_type_name')
        )

        # Build version and comment widget
        version_and_comment = QtWidgets.QWidget()
        version_and_comment.setLayout(QtWidgets.QVBoxLayout())
        version_and_comment.layout().addWidget(
            QtWidgets.QLabel('Version information')
        )
        # Build status selector

        status_layout = QtWidgets.QHBoxLayout()
        status_layout.setAlignment(QtCore.Qt.AlignTop)

        self._asset_status_label = QtWidgets.QLabel("Status")
        self._asset_status_label.setObjectName('gray')

        self._status_selector = StatusSelector()

        status_layout.addWidget(self._asset_status_label)
        status_layout.addWidget(self._status_selector, 10)

        status_layout.addStretch()

        version_and_comment.layout().addLayout(status_layout)

        # Build comments widget
        comments_layout = QtWidgets.QHBoxLayout()
        comments_layout.setContentsMargins(0, 0, 0, 0)

        comment_label = QtWidgets.QLabel('Description')
        comment_label.setObjectName('gray')
        comment_label.setAlignment(QtCore.Qt.AlignTop)
        self._comments_input = QtWidgets.QTextEdit()
        self._comments_input.setMaximumHeight(40)
        self._comments_input.setPlaceholderText("Type a description...")

        comments_layout.addWidget(comment_label)
        comments_layout.addWidget(self._comments_input)

        version_and_comment.layout().addLayout(comments_layout)

        # Add the widgets to the layout
        self.layout().addWidget(self._label)
        self.layout().addLayout(asset_layout)
        self.layout().addWidget(LineWidget())
        self.layout().addWidget(version_and_comment)

    def post_build_ui(self):
        '''Hook up events for the widget.'''
        self._asset_version_selector.assets_added.connect(
            self._on_assets_added
        )
        self._asset_version_selector.selected_item_changed.connect(
            self._on_selected_item_changed_callback
        )
        self._asset_version_selector.new_asset.connect(
            self._on_new_asset_callback
        )
        self._comments_input.textChanged.connect(self._on_comment_updated)
        self._status_selector.currentIndexChanged.connect(
            self._on_status_changed
        )

    def populate(self):
        '''Fetch info from plugin to populate the widget'''
        self.query_assets()

    def query_assets(self):
        '''Query assets based on the context and asset type.'''
        payload = {
            'context_id': self.context_id,
            'asset_type_name': self.plugin_config['options'].get(
                'asset_type_name'
            ),
        }
        self.run_ui_hook(payload)

    @invoke_in_qt_main_thread
    def ui_hook_callback(self, ui_hook_result):
        '''Update the asset and status selectors based on the UI hook result.'''
        super(PublisherAssetVersionSelectorWidget, self).ui_hook_callback(
            ui_hook_result
        )
        self._asset_version_selector.set_assets(ui_hook_result['assets'])
        self._status_selector.set_statuses(ui_hook_result['statuses'])

    def _on_assets_added(self, assets):
        '''Update the label based on the number of assets found.'''
        if len(assets or []) > 0:
            self._label.setText(
                'We found {} asset{} published on this task. '
                'Choose version'.format(
                    len(assets),
                    's' if len(assets) > 1 else '',
                )
            )
        else:
            self._label.setText('<html><i>No assets found!<i></html>')

    def _on_selected_item_changed_callback(self, version, asset_id):
        '''Update the plugin options based on the selected item.'''
        self.set_plugin_option('context_id', self.context_id)
        if not version:
            self.set_plugin_option('asset_version_id', None)
            self.set_plugin_option('asset_id', asset_id)
            return
        self.set_plugin_option('asset_version_id', version.get('id'))
        self.set_plugin_option('asset_id', asset_id)
        self._status_selector.set_status_by_name(version.get('status'))

    def _on_new_asset_callback(self, asset_name):
        '''Update the plugin options based on the new asset name.'''
        self.set_plugin_option('context_id', self.context_id)
        self.set_plugin_option('asset_version_id', None)
        self.set_plugin_option('asset_id', None)
        self.set_plugin_option('asset_name', asset_name)

    def _on_status_changed(self, index):
        '''Update the plugin options based on the selected status.'''
        status_dict = self._status_selector.status
        if status_dict:
            self.set_plugin_option('status_id', status_dict['id'])

    def _on_comment_updated(self):
        '''Update the plugin options based on the current comment.'''
        current_text = self.comments_input.toPlainText()
        self.set_plugin_option('comment', current_text)
