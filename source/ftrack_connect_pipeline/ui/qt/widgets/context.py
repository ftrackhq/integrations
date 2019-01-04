from QtExt import QtWidgets
from ftrack_connect_pipeline.ui.qt.widgets.simple import SimpleWidget
from ftrack_connect.ui.widget import entity_selector
from ftrack_connect.ui.widget import asset_options
from ftrack_connect.ui.widget import header


class ContextWidget(SimpleWidget):
    def __init__(self, parent=None, session=None, data=None, name=None, description=None, options=None, call_topic=None):
        self.assetOptions = None
        self.entitySelector = None
        self.widget_options = {}
        self.header = header.Header(session.api_user)
        super(ContextWidget, self).__init__(parent=parent, session=session, data=data, name=name, description=description, options=options, call_topic=call_topic)
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
        # self.assetCreated.connect(self.assetOptions.setAsset)
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
                result['asset_type'] = widget.getAssetType().getShort()

        return result