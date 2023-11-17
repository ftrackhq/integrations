# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from Qt import QtWidgets, QtCore, QtGui

from ftrack_framework_qt.widgets import BaseWidget

from ftrack_qt.widgets.selectors import AssetSelector
from ftrack_qt.widgets.selectors import StatusSelector
from ftrack_qt.widgets.lines import LineWidget


# TODO: review and docstring this code
class PublishContextWidget(BaseWidget):
    '''Main class to represent a context widget on a publish process.'''

    name = 'publisher_context_selector'
    ui_type = 'qt'

    def __init__(
        self,
        event_manager,
        client_id,
        context_id,
        plugin_config,
        group_config,
        on_set_plugin_option,
        parent=None,
    ):
        '''initialise PublishContextWidget with *parent*, *session*, *data*,
        *name*, *description*, *options* and *context*
        '''
        self._asset_selector = None
        self._asset_status_label = None
        self._status_selector = None
        self._comments_input = None

        super(PublishContextWidget, self).__init__(
            event_manager,
            client_id,
            context_id,
            plugin_config,
            group_config,
            on_set_plugin_option,
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

        asset_layout = QtWidgets.QVBoxLayout()
        asset_layout.setAlignment(QtCore.Qt.AlignTop)

        # Create asset
        self._asset_selector = AssetSelector(
            AssetSelector.MODE_SELECT_ASSET_CREATE,
            self._on_fetch_assets_callback,
            self.session,
        )
        asset_layout.addWidget(self._asset_selector)
        # set the current context
        self.set_context()

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
        self.layout().addLayout(asset_layout)
        self.layout().addWidget(LineWidget())
        self.layout().addWidget(version_and_comment)

    def post_build_ui(self):
        '''hook events'''
        self._asset_selector.assetChanged.connect(self._on_asset_changed)
        self._comments_input.textChanged.connect(self._on_comment_updated)
        self._status_selector.currentIndexChanged.connect(
            self._on_status_changed
        )

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

    def set_context(self):
        self._asset_selector.set_asset_name(
            self.plugin_config['options'].get('asset_type_name'),
        )
        self._asset_selector.reload()

    def _on_fetch_assets_callback(self):
        '''Return publishable assets back to asset selector'''
        # TODO: To be moved to a plugin when ui_hook is implemented
        context_id = self.context_id

        asset_type_entity = self.session.query(
            'select name from AssetType where short is "{}"'.format(
                self.plugin_options.get('asset_type_name')
            )
        ).first()

        # Determine if we have a task or not
        context = self.session.get('Context', context_id)
        # If it's a fake asset, context will be None so return empty list.
        if not context:
            return []
        if context.entity_type == 'Task':
            assets = self.session.query(
                'select name, versions.task.id, type.id, id, latest_version,'
                'latest_version.version '
                'from Asset where versions.task.id is {} and type.id is {}'.format(
                    context_id, asset_type_entity['id']
                )
            ).all()
        else:
            assets = self.session.query(
                'select name, versions.task.id, type.id, id, latest_version,'
                'latest_version.version '
                'from Asset where parent.id is {} and type.id is {}'.format(
                    context_id, asset_type_entity['id']
                )
            ).all()
        return list(assets)
