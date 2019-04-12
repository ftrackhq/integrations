from qtpy import QtWidgets, QtCore


class AssetSelector(QtWidgets.QWidget):

    def __init__(self, session, asset_type, parent=None):
        super(AssetSelector, self).__init__(parent=parent)
        self._context = None
        self.session = session
        self.asset_type = asset_type

        self.radioButtonFrame = QtWidgets.QFrame()
        self.radioButtonFrame.setLayout(QtWidgets.QHBoxLayout())
        self.radioButtonFrame.layout().setContentsMargins(5, 5, 5, 5)

        self.newAssetButton = QtWidgets.QRadioButton('Create new')
        self.newAssetButton.toggled.connect(self._onNewAssetToggled)
        self.radioButtonFrame.layout().addWidget(self.newAssetButton)

        self.existingAssetButton = QtWidgets.QRadioButton('Version up existing')
        self.existingAssetButton.toggled.connect(self._onExistingAssetToggled)
        self.radioButtonFrame.layout().addWidget(self.existingAssetButton)
        #
        # self.existingAssetSelector = _asset_selector.AssetSelector()
        # self.assetNameLineEdit = _asset_name_edit.AssetNameEdit(
        #     self.existingAssetSelector, self.assetTypeSelector
        # )

        self.assetNameLineEdit.textEdited.connect(self._onAssetNameEdited)

    def setContext(self, entity):
        '''Clear and reload existing assets when entity changes.'''
        self._context = entity
        self.existingAssetSelector.clear()
        if self._context:
            self.existingAssetSelector.loadAssets(self._context)