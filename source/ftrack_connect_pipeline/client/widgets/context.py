# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack
from functools import partial
from QtExt import QtWidgets
from ftrack_connect_pipeline.client.widgets.simple import BaseWidget

from ftrack_connect.ui.widget import entity_selector
from ftrack_connect.ui.widget import asset_options
from ftrack_connect.ui.widget import context_selector
from ftrack_connect.ui.widget import list_assets_table
from ftrack_connect.ui.widget import component_table


# dummy wrap to make old class work
class ConnectorWrapper(object):

    def __init__(self, session):
        self.session = session

    def getConnectorName(self):
        return "foobar"


class PublishContextWidget(BaseWidget):
    def __init__(self, parent=None, session=None, data=None, name=None, description=None, options=None):
        super(PublishContextWidget, self).__init__(parent=parent, session=session, data=data, name=name, description=description, options=options)

    def build(self):
        super(PublishContextWidget, self).build()
        self._build_context_id_selector()
        self._build_asset_selector()

    def post_build(self):
        self.entitySelector.entityChanged.connect(self.assetOptions.setEntity)

    def _set_context_option_result(self, entity, key):
        self.set_option_result(entity.getId(), key=key)

    def _build_context_id_selector(self):
        self.context_layout = QtWidgets.QHBoxLayout()
        self.context_layout.setContentsMargins(0, 0, 0, 0)

        self.layout().addLayout(self.context_layout)
        self.entitySelector = entity_selector.EntitySelector()
        self.context_layout.addWidget(self.entitySelector)
        self.register_widget('context_id', self.entitySelector)
        update_fn = partial(self._set_context_option_result, key='context_id')

        self.entitySelector.entityChanged.connect(update_fn)

    def _build_asset_selector(self):
        self.asset_layout = QtWidgets.QFormLayout()
        self.asset_layout.setContentsMargins(0, 0, 0, 0)

        self.assetOptions = asset_options.AssetOptions()
        self.assetOptions.assetTypeSelector.setDisabled(True)

        self.asset_layout.addRow('Asset', self.assetOptions.radioButtonFrame)
        self.asset_layout.addRow('Existing asset', self.assetOptions.existingAssetSelector)
        self.asset_layout.addRow('Type', self.assetOptions.assetTypeSelector)
        self.asset_layout.addRow('Name', self.assetOptions.assetNameLineEdit)
        self.assetOptions.initializeFieldLabels(self.asset_layout)

        self.layout().addLayout(self.asset_layout, stretch=0)
        self.register_widget('asset_name', self.assetOptions)

        update_fn = partial(self._set_context_option_result, key='asset_name')
        self.assetOptions.assetNameLineEdit.textEdited.connect(update_fn)


class LoadContextWidget(BaseWidget):

    def __init__(self, parent=None, session=None, data=None, name=None, description=None, options=None):
        self._connector_wrapper = ConnectorWrapper(session)
        super(LoadContextWidget, self).__init__(parent=parent, session=session, data=data, name=name, description=description, options=options)

    def _build_others(self):
        self.listAssetsTableWidget = list_assets_table.ListAssetsTableWidget(self)
        self.browseTasksWidget = context_selector.ContextSelector(
            currentEntity=None, parent=self
        )
        self.componentTableWidget = component_table.ComponentTableWidget(self, self._connector_wrapper)
        self.browseTasksWidget.entityChanged.connect(self.clickedIdSignal)
        self.listAssetsTableWidget.assetVersionSelectedSignal[str].connect(
            self.clickedAssetVSignal
        )

        self.layout().addWidget(self.browseTasksWidget, stretch=0)
        self.layout().addWidget(self.listAssetsTableWidget, stretch=4)
        self.layout().addWidget(self.componentTableWidget, stretch=4)

    def selectedComponents(self):
        '''Import selected components.'''

        selectedRows = self.componentTableWidget.selectionModel(
        ).selectedRows()
        components_id = []
        for r in selectedRows:
            componentItem = self.componentTableWidget.item(
                r.row(),
                self.componentTableWidget.columns.index('Component')
            )
            component_id = componentItem.data(
                self.componentTableWidget.COMPONENT_ROLE
            )
            components_id.append(component_id)
        return components_id

    def clickedIdSignal(self, ftrackId):
        '''Handle click signal.'''
        self.listAssetsTableWidget.initView(ftrackId)

    def clickedAssetVSignal(self, assetVid):
        '''Set asset version to *assetVid*.'''
        self.componentTableWidget.setAssetVersion(assetVid)

    def _build_component_selector(self, value):
        self.widgets['component_list'] = self.selectedComponents

    def build(self):
        super(LoadContextWidget, self).build()
        self._build_others()
        self._build_component_selector(self.options['component_list'])

    def value(self):
        result = {}
        for label, widget in self.widgets.items():
            result[label] = widget()
        return result