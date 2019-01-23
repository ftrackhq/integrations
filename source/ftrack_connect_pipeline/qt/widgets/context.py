from QtExt import QtWidgets
from ftrack_connect_pipeline.qt.widgets.simple import SimpleWidget

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


class PublishContextWidget(SimpleWidget):
    def __init__(self, parent=None, session=None, data=None, name=None, description=None, options=None, plugin_topic=None):
        self.assetOptions = None
        self.entitySelector = None
        super(PublishContextWidget, self).__init__(parent=parent, session=session, data=data, name=name, description=description, options=options, plugin_topic=plugin_topic)
        self.entitySelector.entityChanged.connect(self.assetOptions.setEntity)

    def _build_context_id_selector(self, value):
        option_layout = QtWidgets.QHBoxLayout()
        self.layout().addLayout(option_layout)
        self.entitySelector = entity_selector.EntitySelector()
        option_layout.addWidget(self.entitySelector)
        self.widget_options['context_id'] = self.entitySelector

    def _build_asset_selector(self, value):
        option_layout = QtWidgets.QFormLayout()

        self.assetOptions = asset_options.AssetOptions()
        self.entitySelector.entityChanged.connect(self.assetOptions.setEntity)
        self.assetOptions.assetTypeSelector.setDisabled(True)

        option_layout.addRow('Asset', self.assetOptions.radioButtonFrame)
        option_layout.addRow('Existing asset', self.assetOptions.existingAssetSelector)
        option_layout.addRow('Type', self.assetOptions.assetTypeSelector)
        option_layout.addRow('Name', self.assetOptions.assetNameLineEdit)
        self.assetOptions.initializeFieldLabels(option_layout)

        self.widget_options['asset_name'] = self.assetOptions
        self.layout().addLayout(option_layout, stretch=0)

    def build_options(self, options):
        self._build_context_id_selector(options['context_id'])
        self._build_asset_selector(options['asset_name'])

    def extract_options(self):
        result = {}
        for label, widget in self.widget_options.items():
            if label == 'context_id':
                result[label] = widget._entity.getId()
            else:
                result[label] = widget.getAssetName()
        return result


class LoadContextWidget(SimpleWidget):

    def __init__(self, parent=None, session=None, data=None, name=None, description=None, options=None, plugin_topic=None):
        self._connector_wrapper = ConnectorWrapper(session)
        super(LoadContextWidget, self).__init__(parent=parent, session=session, data=data, name=name, description=description, options=options, plugin_topic=plugin_topic)

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
        self.widget_options['component_list'] = self.selectedComponents

    def build_options(self, options):
        self._build_others()
        self._build_component_selector(options['component_list'])

    def extract_options(self):
        result = {}
        for label, widget in self.widget_options.items():
            result[label] = widget()
        return result