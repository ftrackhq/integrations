# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import os
from Qt import QtWidgets, QtCore, QtGui
from ftrack_connect_pipeline_qt.client.widgets.options import BaseOptionsWidget

from ftrack_connect_pipeline_qt.ui.widget.context_selector import ContextSelector
from ftrack_connect_pipeline_qt.ui.widget.asset_selector import AssetSelector
from ftrack_connect_pipeline.utils import get_current_context


class PublishContextWidget(BaseOptionsWidget):
    '''Main class to represent a context widget on a publish process'''

    @property
    def asset_type(self):
        return self._asset_type

    def __init__(
            self, parent=None, session=None, data=None, name=None,
            description=None, options=None, context=None
    ):
        '''initialise PublishContextWidget with *parent*, *session*, *data*,
        *name*, *description*, *options*
        '''

        super(PublishContextWidget, self).__init__(
            parent=parent, session=session, data=data, name=name,
            description=description, options=options, context=context
        )
        self.asset_selector.set_context(self.context)

    def build(self):
        '''build function widgets.'''
        super(PublishContextWidget, self).build()
        self._build_context_id_selector()
        self._build_asset_selector()
        self._build_status_selector()
        self._build_comments_input()

    def post_build(self):
        '''hook events'''
        super(PublishContextWidget, self).post_build()
        self.context_selector.entityChanged.connect(self._on_context_changed)
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

    def _on_context_changed(self, context):
        '''Updates the option dicctionary with provided *context* when
        entityChanged of context_selector event is triggered'''
        self.set_option_result(context['id'], key='context_id')
        self.asset_selector.set_context(context)

    def _on_asset_changed(self, asset_name):
        '''Updates the option dicctionary with provided *asset_name* when
        asset_changed of asset_selector event is triggered'''
        self.set_option_result(asset_name, key='asset_name')

    def _build_context_id_selector(self):
        '''Builds the context_selector widget'''
        self.context_layout = QtWidgets.QHBoxLayout()
        self.context_layout.setContentsMargins(0, 0, 0, 0)

        self.layout().addLayout(self.context_layout)
        self.context_selector = ContextSelector(self.session)
        self.context_selector.setEntity(self.context)

        self.context_layout.addWidget(self.context_selector)
        if self.context:
            self.set_option_result(self.context['id'], key='context_id')

    def _build_asset_selector(self):
        '''Builds the asset_selector widget'''
        self.asset_layout = QtWidgets.QHBoxLayout()
        self.asset_layout.setContentsMargins(0, 0, 0, 0)

        self.asset_selector = AssetSelector(self.session, self.asset_type)
        self.asset_layout.addWidget(self.asset_selector)
        self.layout().addLayout(self.asset_layout)
        current_asset = self.asset_selector.asset_combobox.currentText()
        self.set_option_result(current_asset, key='asset_name')

    def _build_status_selector(self):
        '''Builds the status_selector widget'''
        self.status_layout = QtWidgets.QHBoxLayout()
        self.status_layout.setContentsMargins(0, 0, 0, 0)

        self.status_selector = QtWidgets.QComboBox()
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
        project = self.session.get('Context', self.context['link'][0]['id'])
        schema = project['project_schema']
        statuses = schema.get_statuses('AssetVersion')
        return statuses

    def _build_comments_input(self):
        '''Builds the comments_container widget'''
        self.comments_container = QtWidgets.QGroupBox('Comment')

        self.comments_layout = QtWidgets.QHBoxLayout()

        self.comments_input = QtWidgets.QTextEdit()
        self.comments_layout.addWidget(self.comments_input)
        self.comments_container.setLayout(self.comments_layout)

        self.layout().addWidget(self.comments_container)
        current_text = self.comments_input.toPlainText()
        if current_text:
            self.set_option_result(current_text, key='comment')




class LoadContextWidget(BaseOptionsWidget):

    def __init__(self, parent=None, session=None, data=None, name=None,
                 description=None, options=None):
        super(LoadContextWidget, self).__init__(
            parent=parent, session=session, data=data, name=name,
            description=description, options=options
        )