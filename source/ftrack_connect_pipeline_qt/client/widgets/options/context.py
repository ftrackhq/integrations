# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

import os
from Qt import QtWidgets, QtCore, QtGui
from ftrack_connect_pipeline_qt.client.widgets.options import BaseOptionsWidget

from ftrack_connect_pipeline_qt.ui.utility.widget.asset_selector import AssetSelector
from ftrack_connect_pipeline_qt.ui.utility.widget.version_selector import VersionSelector
from ftrack_connect_pipeline_qt.ui.utility.widget.thumbnail import AssetVersion as AssetVersionThumbnail
from ftrack_connect_pipeline_qt.ui.utility.widget.entity_info import VersionInfo
from ftrack_connect_pipeline_qt.ui.utility.widget.asset_grid_selector import AssetGridSelector
from ftrack_connect_pipeline_qt.utils import BaseThread



class PublishContextWidget(BaseOptionsWidget):
    '''Main class to represent a context widget on a publish process'''

    def __init__(
            self, parent=None, session=None, data=None, name=None,
            description=None, options=None, context_id=None, asset_type_name=None
    ):
        '''initialise PublishContextWidget with *parent*, *session*, *data*,
        *name*, *description*, *options* and *context*
        '''

        super(PublishContextWidget, self).__init__(
            parent=parent, session=session, data=data, name=name,
            description=description, options=options, context_id=context_id,
            asset_type_name=asset_type_name
        )
        self.asset_selector.set_context(context_id, asset_type_name)

    def build(self):
        '''build function widgets.'''
        if self.context_id:
            self.set_option_result(self.context_id, key='context_id')
        self._build_asset_selector()
        self._build_status_selector()
        self._build_comments_input()

    def post_build(self):
        '''hook events'''
        super(PublishContextWidget, self).post_build()
        self.asset_selector.asset_changed.connect(self._on_asset_changed)
        self.comments_input.textChanged.connect(self._on_comment_updated)
        self.status_selector.currentIndexChanged.connect(self._on_status_changed)

    def _on_status_changed(self, status):
        '''Updates the options dictionary with provided *status* when
        currentIndexChanged of status_selector event is triggered'''
        status_id = self.status_selector.itemData(status)
        self.set_option_result(status_id, key='status_id')

    def _on_comment_updated(self):
        '''Updates the option dicctionary with current text when
        textChanged of comments_input event is triggered'''
        current_text = self.comments_input.text()
        self.set_option_result(current_text, key='comment')

    def _on_asset_changed(self, asset_name, asset_entity, is_valid):
        '''Updates the option dicctionary with provided *asset_name* when
        asset_changed of asset_selector event is triggered'''
        self.set_option_result(asset_name, key='asset_name')
        self.set_option_result(asset_entity['id'], key='asset_id')
        self.set_option_result(is_valid, key='is_valid_name')
        self.asset_changed.emit(asset_name, asset_entity['id'], is_valid)

    def _build_asset_selector(self):
        '''Builds the asset_selector widget'''
        self.asset_layout = QtWidgets.QVBoxLayout()
        self.asset_layout.setContentsMargins(0, 0, 0, 0)
        self.asset_layout.setAlignment(QtCore.Qt.AlignTop)

        self.asset_selector = AssetSelector(self.session)
        self.asset_layout.addWidget(self.asset_selector)
        self.layout().addLayout(self.asset_layout)

    def _build_status_selector(self):
        '''Builds the status_selector widget'''
        self.status_layout = QtWidgets.QVBoxLayout()
        self.status_layout.setContentsMargins(0, 0, 0, 0)
        self.status_layout.setAlignment(QtCore.Qt.AlignTop)

        self.asset_status_label = QtWidgets.QLabel("Status")

        self.status_selector = QtWidgets.QComboBox()
        self.status_selector.setEditable(False)

        self.status_layout.addWidget(self.asset_status_label)
        self.status_layout.addWidget(self.status_selector)
        self.layout().addLayout(self.status_layout)

        thread = BaseThread(
            name='get_status_thread',
            target=self._get_statuses,
            callback=self.set_statuses,
            target_args=()
        )
        thread.start()

    def set_statuses(self, statuses):
        for index, status in enumerate(statuses):
            pixmap_status = QtGui.QPixmap(13, 13)
            pixmap_status.fill(QtGui.QColor(status['color']))
            self.status_selector.addItem(pixmap_status, status['name'], status['id'])

        if statuses:
            self.set_option_result(statuses[0]['id'], key='status_id')

    def _get_statuses(self):
        '''Returns the status of the selected assetVersion'''
        context_entity = self.session.query(
                'select link, name , parent, parent.name from Context where id is "{}"'.format(self.context_id)
            ).one()

        project = self.session.query(
            'select name , parent, parent.name from Context where id is "{}"'.format(
                context_entity['link'][0]['id']
            )
        ).one()

        schema = project['project_schema']
        statuses = schema.get_statuses('AssetVersion')
        return statuses

    def _build_comments_input(self):
        '''Builds the comments_container widget'''
        self.coments_layout = QtWidgets.QVBoxLayout()
        self.coments_layout.setContentsMargins(0, 0, 0, 0)
        self.coments_layout.setAlignment(QtCore.Qt.AlignTop)

        self.asset_status_label = QtWidgets.QLabel("Comment")


        comment_label = QtWidgets.QLabel('Comment')
        self.comments_input = QtWidgets.QLineEdit()
        self.comments_input.setPlaceholderText("Type a comment...")
        self.comments_input.setStyleSheet(
            "border: none;"
            "background-color: transparent;"
        )

        self.coments_layout.addWidget(comment_label)
        self.coments_layout.addWidget(self.comments_input)
        self.layout().addLayout(self.coments_layout)

        current_text = self.comments_input.text()
        if current_text:
            self.set_option_result(current_text, key='comment')


class LoadContextWidget(BaseOptionsWidget):
    '''Main class to represent a context widget on a publish process'''

    def __init__(
            self, parent=None, session=None, data=None, name=None,
            description=None, options=None, context_id=None, asset_type_name=None
    ):
        '''initialise PublishContextWidget with *parent*, *session*, *data*,
        *name*, *description*, *options*
        '''

        super(LoadContextWidget, self).__init__(
            parent=parent, session=session, data=data, name=name,
            description=description, options=options, context_id=context_id,
            asset_type_name=asset_type_name
        )

        self.asset_grid_selector.set_context(context_id, asset_type_name)

    def pre_build(self):
        super(LoadContextWidget, self).pre_build()
        self.main_layout = QtWidgets.QVBoxLayout()
        self.layout().addLayout(self.main_layout)

    def build(self):
        '''build function widgets.'''
        if self.context_id:
            self.set_option_result(self.context_id, key='context_id')

        self._build_asset_grid_selector()

    def post_build(self):
        '''hook events'''
        super(LoadContextWidget, self).post_build()
        # self.asset_grid_selector.assets_query_done.connect(self._pre_select_asset)
        self.asset_grid_selector.asset_changed.connect(self._on_asset_changed)

    def _on_asset_changed(self, asset_name, asset_entity, asset_version_id, version_num):
        '''Updates the option dicctionary with provided *asset_name* when
        asset_changed of asset_selector event is triggered'''
        self.set_option_result(asset_name, key='asset_name')
        self.set_option_result(asset_entity['id'], key='asset_id')
        self.set_option_result(version_num, key='version_number')
        self.set_option_result(asset_version_id, key='version_id')
        self.asset_changed.emit(asset_name, asset_entity['id'], True)

    def _build_asset_grid_selector(self):
        label = QtWidgets.QLabel("Choose which asset and version to load")
        self.asset_grid_selector = AssetGridSelector(self.session)

        self.main_layout.addWidget(label)
        self.main_layout.addWidget(self.asset_grid_selector)

