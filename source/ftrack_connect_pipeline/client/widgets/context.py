# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import os
from functools import partial
from qtpy import QtWidgets
from ftrack_connect_pipeline.client.widgets.simple import BaseWidget

from ftrack_connect_pipeline.ui.widget.context_selector import ContextSelector
from ftrack_connect_pipeline.ui.widget.asset_selector import AssetSelector


class PublishContextWidget(BaseWidget):
    def __init__(self, parent=None, session=None, data=None, name=None, description=None, options=None):
        super(PublishContextWidget, self).__init__(parent=parent, session=session, data=data, name=name, description=description, options=options)

    def build(self):
        '''build function widgets.'''
        super(PublishContextWidget, self).build()
        self._build_context_id_selector()
        # self._build_asset_selector()

    def get_current_context(self):
        '''return an api object representing the current context.'''
        context_id = os.getenv(
            'FTRACK_CONTEXTID',
                os.getenv('FTRACK_TASKID',
                    os.getenv('FTRACK_SHOTID'
                )
            )
        )
        current_entity = self.session.get('Context', context_id)
        return current_entity

    def post_build(self):
        '''hook events'''
        # self.entitySelector.entityChanged.connect(self.assetOptions.setEntity)

    def _set_context_option_result(self, entity, key):
        self.set_option_result(entity.getId(), key=key)

    def _build_context_id_selector(self):
        self.context_layout = QtWidgets.QHBoxLayout()
        self.context_layout.setContentsMargins(0, 0, 0, 0)

        self.layout().addLayout(self.context_layout)
        current_context = self.get_current_context()
        self.context_selector = ContextSelector(self.session)
        self.context_selector.setEntity(current_context)

        self.context_layout.addWidget(self.context_selector)
        # update_fn = partial(self._set_context_option_result, key='context_id')
        #
        # self.entitySelector.entityChanged.connect(update_fn)
        # self.set_option_result(self.get_current_context().getId(), 'context_id')
    #
    def _build_asset_selector(self):
        self.asset_layout = QtWidgets.QFormLayout()
        self.asset_layout.setContentsMargins(0, 0, 0, 0)

        self.asset_selector = AssetSelector(self.session)
        self.asset_layout.addWidget(self.asset_selector)
        self.layout().addLayout(self.asset_layout, stretch=0)

    #     self.asset_layout.addRow('Asset', self.assetOptions.radioButtonFrame)
    #     self.asset_layout.addRow('Existing asset', self.assetOptions.existingAssetSelector)
    #     self.asset_layout.addRow('Type', self.assetOptions.assetTypeSelector)
    #     self.asset_layout.addRow('Name', self.assetOptions.assetNameLineEdit)
    #     self.assetOptions.initializeFieldLabels(self.asset_layout)
    #
    #     update_fn = partial(self.set_option_result, key='asset_name')
    #     self.assetOptions.assetNameLineEdit.textEdited.connect(update_fn)


class LoadContextWidget(BaseWidget):

    def __init__(self, parent=None, session=None, data=None, name=None, description=None, options=None):
        self._connector_wrapper = ConnectorWrapper(session)
        super(LoadContextWidget, self).__init__(parent=parent, session=session, data=data, name=name, description=description, options=options)