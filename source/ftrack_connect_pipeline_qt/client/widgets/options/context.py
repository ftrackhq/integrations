# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

import os
from Qt import QtWidgets, QtCore, QtGui
from ftrack_connect_pipeline_qt.client.widgets.options import BaseOptionsWidget

from ftrack_connect_pipeline_qt.ui.utility.widget.context_selector import ContextSelector
from ftrack_connect_pipeline_qt.ui.utility.widget.asset_selector import AssetSelector
from ftrack_connect_pipeline_qt.ui.utility.widget.version_selector import VersionSelector
from ftrack_connect_pipeline_qt.ui.utility.widget.thumbnail import AssetVersion as AssetVersionThumbnail

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
        self.asset_selector.set_context(self.context_entity, self.asset_type_entity)

    def build(self):
        '''build function widgets.'''
        if self.context_entity:
            self.set_option_result(self.context_entity['id'], key='context_id')
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
        self.asset_layout = QtWidgets.QHBoxLayout()
        self.asset_layout.setContentsMargins(0, 0, 0, 0)
        self.asset_layout.setAlignment(QtCore.Qt.AlignTop)

        self.asset_selector = AssetSelector(self.session)
        self.asset_layout.addWidget(self.asset_selector)
        self.layout().addLayout(self.asset_layout)
        current_asset = self.asset_selector.asset_combobox.currentText()
        self.set_option_result(current_asset, key='asset_name')
        is_valid = self.asset_selector.asset_combobox.validate_name()
        self.set_option_result(is_valid, key='is_valid_name')

    def _build_status_selector(self):
        '''Builds the status_selector widget'''
        self.status_layout = QtWidgets.QVBoxLayout()
        self.status_layout.setContentsMargins(0, 0, 0, 0)
        self.status_layout.setAlignment(QtCore.Qt.AlignTop)

        self.asset_status_label = QtWidgets.QLabel("Asset Status")
        self.status_selector = QtWidgets.QComboBox()
        self.status_selector.setEditable(False)
        self.status_layout.addWidget(self.asset_status_label)
        self.status_layout.addWidget(self.status_selector)
        self.layout().addLayout(self.status_layout)
        statuses = self._get_statuses()
        for index, status in enumerate(statuses):
            self.status_selector.addItem(status['name'], status['id'])
            status_color = status['color']
            self.status_selector.setItemData(
                index,
                QtGui.QColor(status_color),
                QtCore.Qt.BackgroundColorRole
            )

        if statuses:
            self.set_option_result(statuses[0]['id'], key='status_id')

    def _get_statuses(self):
        '''Returns the status of the selected assetVersion'''
        project = self.session.query(
            'select name , parent, parent.name from Context where id is "{}"'.format(
                self.context_entity['link'][0]['id']
            )
        ).one()

        schema = project['project_schema']
        statuses = schema.get_statuses('AssetVersion')
        return statuses

    def _build_comments_input(self):
        '''Builds the comments_container widget'''
        self.comments_container = QtWidgets.QGroupBox('Comment')

        self.comments_container.setMaximumHeight(150)

        self.comments_layout = QtWidgets.QHBoxLayout()

        self.comments_input = QtWidgets.QTextEdit()
        self.comments_layout.addWidget(self.comments_input)
        self.comments_container.setLayout(self.comments_layout)

        self.layout().addWidget(self.comments_container)
        current_text = self.comments_input.toPlainText()
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

        self.asset_selector.set_context(self.context_entity, self.asset_type_entity)

    def pre_build(self):
        super(LoadContextWidget, self).pre_build()
        layout = QtWidgets.QHBoxLayout()
        self.setLayout(layout)

    def build(self):
        '''build function widgets.'''
        super(LoadContextWidget, self).build()
        if self.context_entity:
            self.set_option_result(self.context_entity['id'], key='context_id')

        self.thumbnail_widget = AssetVersionThumbnail(self.session)
        self.thumbnail_widget.setMinimumWidth(150)
        self.thumbnail_widget.setMinimumHeight(150)
        self.layout().addWidget(self.thumbnail_widget)

        self.selector_layout = QtWidgets.QVBoxLayout()
        self.layout().addLayout(self.selector_layout)

        self._build_asset_selector()
        self._build_version_selector()

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
        self.version_selector.set_context(self.context_entity)
        self.version_selector.set_asset_id(asset_id)
        self.asset_changed.emit(asset_name, asset_id, is_valid)

    def _on_version_changed(self, version_num, version_id):
        '''Updates the option dicctionary with provided *version_number* when
        version_changed of version_selector event is triggered'''
        self.set_option_result(version_num, key='version_number')
        self.set_option_result(version_id, key='version_id')
        self.asset_version_changed.emit(version_id)
        print('Thumb for {}'.format(version_id))
        self.thumbnail_widget.load(version_id)

    def _build_asset_selector(self):
        '''Builds the asset_selector widget'''
        self.asset_selector = AssetSelector(self.session)
        self.asset_selector.asset_combobox.setEditable(False)
        self.selector_layout.addWidget(self.asset_selector)

        asset_name = self.asset_selector.asset_combobox.currentText()
        current_idx = self.asset_selector.asset_combobox.currentIndex()
        asset_id = self.asset_selector.asset_combobox.itemData(current_idx)
        is_valid = self.asset_selector.asset_combobox.validate_name()
        self.set_option_result(asset_name, key='asset_name')
        self.set_option_result(asset_id, key='asset_id')
        self.set_option_result(is_valid, key='is_valid_name')

    def _build_version_selector(self):
        '''Builds the asset_selector widget'''
        self.version_selector = VersionSelector(self.session)
        self.selector_layout.addWidget(self.version_selector)

        version_num = self.version_selector.version_combobox.currentText()
        current_idx = self.version_selector.version_combobox.currentIndex()
        version_id = self.version_selector.version_combobox.itemData(current_idx)
        self.set_option_result(version_num, key='version_number')
        self.set_option_result(version_id, key='version_id')
        self.asset_version_changed.emit(version_id)
