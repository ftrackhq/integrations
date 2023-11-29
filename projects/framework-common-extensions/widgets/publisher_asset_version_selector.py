# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from Qt import QtWidgets, QtCore, QtGui

from ftrack_framework_qt.widgets import BaseWidget

from ftrack_qt.widgets.selectors import PublishAssetSelector
from ftrack_qt.widgets.selectors import StatusSelector
from ftrack_qt.widgets.lines import LineWidget


# TODO: review and docstring this code
class PublisherAssetVersionSelectorWidget(BaseWidget):
    '''Main class to represent a context widget on a publish process.'''

    name = 'publisher_asset_version_selector'
    ui_type = 'qt'
    fetch_method_on_start = 'query_assets'

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
        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(QtCore.Qt.AlignTop)
        self.setLayout(layout)
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed
        )

    def build_ui(self):
        '''build function widgets.'''

        self._label = QtWidgets.QLabel()
        self._label.setObjectName('gray')
        self._label.setWordWrap(True)

        asset_layout = QtWidgets.QVBoxLayout()
        asset_layout.setAlignment(QtCore.Qt.AlignTop)

        # Create asset
        self._asset_version_selector = PublishAssetSelector()
        asset_layout.addWidget(self._asset_version_selector)

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

        self._status_selector = StatusSelector(self.session, self.context_id)

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
        '''hook events'''
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
        # # set context
        # self.set_context()

    def query_assets(self):
        payload = {
            'context_id': self.context_id,
            'asset_type_name': self.plugin_config['options'].get(
                'asset_type_name'
            ),
        }
        self.run_ui_hook(payload)

    def ui_hook_callback(self, ui_hook_result):
        self._asset_version_selector.set_assets(ui_hook_result)

    def _on_assets_added(self, assets):
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

    def _on_selected_item_changed_callback(self, version):
        self.set_plugin_option('context_id', self.context_id)
        self.set_plugin_option('asset_version_id', version['id'])

    def _on_new_asset_callback(self, asset_name):
        self.set_plugin_option('context_id', self.context_id)
        self.set_plugin_option('asset_version_id', None)
        self.set_plugin_option('asset_name', asset_name)

    def _on_status_changed(self, status):
        '''Updates the options dictionary with provided *status* when
        currentIndexChanged of status_selector event is triggered'''
        status_id = self._status_selector.itemData(status)
        self.set_plugin_option('status_id', status_id)

    def _on_comment_updated(self):
        '''Updates the option dictionary with current text when
        textChanged of comments_input event is triggered'''
        current_text = self.comments_input.toPlainText()
        self.set_plugin_option('comment', current_text)

    def _on_asset_changed(self, asset_name, asset_entity, is_valid):
        '''Updates the option dictionary with provided *asset_name* when
        asset_changed of asset_selector event is triggered'''
        self.set_plugin_option('asset_name', asset_name)
        self.set_plugin_option('is_valid_name', is_valid)
        if asset_entity:
            self.set_plugin_option('asset_id', asset_entity['id'])
        else:
            self.set_plugin_option('asset_id', None)

    def set_context(self):
        self.set_plugin_option('context_id', self.context_id)
        self._asset_version_selector.set_asset_name(
            self.plugin_config['options'].get('asset_type_name'),
        )
        self.reload()

    def reload(self):
        '''Reload assets on context'''
        self._asset_version_selector.reload()

    def _on_fetch_assets_callback(self):
        '''Return assets back to asset selector'''
        payload = {
            'context_id': self.context_id,
            'context_type': 'asset',
            'asset_type_name': self.plugin_config['options'].get(
                'asset_type_name'
            ),
        }
        asset_ids = self.run_ui_hook(payload, await_result=True)
        return list(
            self.session.query(
                'select name, versions.task.id, type.id, id, latest_version,'
                'latest_version.version '
                'from Asset where id in ({})'.format(
                    ','.join([str(asset_id) for asset_id in asset_ids])
                )
            ).all()
        )
