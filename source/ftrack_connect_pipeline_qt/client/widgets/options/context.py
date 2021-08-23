# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

import os
from Qt import QtWidgets, QtCore, QtGui
from ftrack_connect_pipeline_qt.client.widgets.options import BaseOptionsWidget

from ftrack_connect_pipeline_qt.ui.utility.widget.asset_selector import AssetSelector
from ftrack_connect_pipeline_qt.ui.utility.widget.version_selector import VersionSelector
from ftrack_connect_pipeline_qt.ui.utility.widget.thumbnail import AssetVersion as AssetVersionThumbnail
from ftrack_connect_pipeline_qt.ui.utility.widget.entity_info import VersionInfo
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
        current_text = self.comments_input.toPlainText()
        self.set_option_result(current_text, key='comment')

    def _on_asset_changed(self, asset_name, asset_id, is_valid):
        '''Updates the option dicctionary with provided *asset_name* when
        asset_changed of asset_selector event is triggered'''
        self.set_option_result(asset_name, key='asset_name')
        self.set_option_result(asset_id, key='asset_id')
        self.set_option_result(is_valid, key='is_valid_name')
        self.asset_changed.emit(asset_name, asset_id, is_valid)

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

        self.asset_selector.set_context(context_id, asset_type_name)

    def pre_build(self):
        super(LoadContextWidget, self).pre_build()
        self.main_layout = QtWidgets.QHBoxLayout()
        self.layout().addLayout(self.main_layout)

    def build(self):
        '''build function widgets.'''
        if self.context_id:
            self.set_option_result(self.context_id, key='context_id')

        self._build_thumbnail()
        self._build_info_widget()
        self._build_asset_version_selector()
        # self._build_asset_selector()
        # self._build_version_selector()

    def post_build(self):
        '''hook events'''
        super(LoadContextWidget, self).post_build()
        self.asset_selector.asset_changed.connect(self._on_asset_changed)
        self.version_selector.version_changed.connect(self._on_version_changed)

    def _on_asset_changed(self, asset_name, asset_id, is_valid):
        '''Updates the option dicctionary with provided *asset_name* when
        asset_changed of asset_selector event is triggered'''
        self.set_option_result(asset_name, key='asset_name')
        self.set_option_result(asset_id, key='asset_id')
        self.set_option_result(is_valid, key='is_valid_name')
        self.version_selector.set_context(self.context_id)
        self.version_selector.set_asset_id(asset_id)
        self.asset_changed.emit(asset_name, asset_id, is_valid)

    def _on_version_changed(self, version_num, version_id):
        if not version_id:
            return

        '''Updates the option dicctionary with provided *version_number* when
        version_changed of version_selector event is triggered'''
        self.set_option_result(version_num, key='version_number')
        self.set_option_result(version_id, key='version_id')
        self.asset_version_changed.emit(version_id)
        self.thumbnail_widget.load(version_id)
        self.info_version.setEntity(version_id)

    def _build_info_widget(self):
        self.info_version = VersionInfo(session=self.session)
        self.main_layout.addWidget(self.info_version)

    def _build_thumbnail(self):
        self.thumbnail_widget = AssetVersionThumbnail(self.session)
        self.thumbnail_widget.setScaledContents(True)
        self.thumbnail_widget.setMaximumHeight(100)
        self.thumbnail_widget.setMaximumWidth(200)

        self.main_layout.addWidget(self.thumbnail_widget)

    def _build_asset_version_selector(self):
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout()
        widget.setLayout(layout)

        self._build_asset_selector(layout)
        self._build_version_selector(layout)
        self.main_layout.addWidget(widget)
        layout.addStretch()

    def _build_asset_selector(self, layout):
        '''Builds the asset_selector widget'''
        self.asset_selector = AssetSelector(self.session)
        layout.addWidget(self.asset_selector)

    def _build_version_selector(self, layout):
        '''Builds the asset_selector widget'''
        self.version_selector = VersionSelector(self.session)
        layout.addWidget(self.version_selector)

        version_num = self.version_selector.version_combobox.currentText()
        current_idx = self.version_selector.version_combobox.currentIndex()
        version_id = self.version_selector.version_combobox.itemData(current_idx)
        self.set_option_result(version_num, key='version_number')
        self.set_option_result(version_id, key='version_id')
        self.asset_version_changed.emit(version_id)

