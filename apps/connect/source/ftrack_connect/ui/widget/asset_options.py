# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import logging

try:
    from PySide6 import QtWidgets
except ImportError:
    from PySide2 import QtWidgets

from ftrack_connect.error import NotUniqueError
from ftrack_connect.ui.widget import asset_name_edit as _asset_name_edit
from ftrack_connect.ui.widget import (
    asset_type_selector as _asset_type_selector,
)
from ftrack_connect.ui.widget import asset_selector as _asset_selector

NEW_ASSET = 'NEW_ASSET'
EXISTING_ASSET = 'EXISTING_ASSET'


class AssetOptions(QtWidgets.QWidget):
    '''Asset options: holds asset related widgets and logic.

    .. note::

        Currently this is not an actual widget due to the need of adding the
        widgets separately in the publisher's form layout in order to get the
        labels / columns to line up.
    '''

    @property
    def session(self):
        '''Return current session.'''
        return self._session

    def __init__(self, session, parent=None):
        '''Instantiate the asset options.'''
        super(AssetOptions, self).__init__(parent=parent)

        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )
        self._session = session
        self._entity = None
        self._hasEditedName = False

        self.radioButtonFrame = QtWidgets.QFrame()
        self.radioButtonFrame.setLayout(QtWidgets.QHBoxLayout())
        self.radioButtonFrame.layout().setContentsMargins(5, 5, 5, 5)

        self.newAssetButton = QtWidgets.QRadioButton('Create new')
        self.newAssetButton.toggled.connect(self._onNewAssetToggled)
        self.radioButtonFrame.layout().addWidget(self.newAssetButton)

        self.existingAssetButton = QtWidgets.QRadioButton(
            'Version up existing'
        )
        self.existingAssetButton.toggled.connect(self._onExistingAssetToggled)
        self.radioButtonFrame.layout().addWidget(self.existingAssetButton)

        self.existingAssetSelector = _asset_selector.AssetSelector(
            session=self.session, parent=parent
        )
        self.assetTypeSelector = _asset_type_selector.AssetTypeSelector(
            session=self.session, parent=parent
        )
        self.assetNameLineEdit = _asset_name_edit.AssetNameEdit(
            self.session,
            self.existingAssetSelector,
            self.assetTypeSelector,
            parent=parent,
        )

        self.assetTypeSelector.currentIndexChanged.connect(
            self._onAssetTypeChanged
        )
        self.assetNameLineEdit.textEdited.connect(self._onAssetNameEdited)

    def initializeFieldLabels(self, layout):
        '''Get labels for widgets in *layout* and set initial state.'''
        self.assetNameLineEdit._fieldLabel = layout.labelForField(
            self.assetNameLineEdit
        )
        self.existingAssetSelector._fieldLabel = layout.labelForField(
            self.existingAssetSelector
        )
        self.assetTypeSelector._fieldLabel = layout.labelForField(
            self.assetTypeSelector
        )
        self._toggleFieldAndLabel(self.existingAssetSelector, False)
        self._toggleFieldAndLabel(self.assetTypeSelector, False)
        self._toggleFieldAndLabel(self.assetNameLineEdit, False)

    def setEntity(self, entity):
        '''Clear and reload existing assets when entity changes.'''
        self._entity = entity
        self.existingAssetSelector.clear()
        if self._entity:
            self.existingAssetSelector.loadAssets(self._entity)

    def setAsset(self, asset=None):
        '''Select *asset*, add it to the selector if it does not exist.'''
        self.logger.debug(
            'Reloading assets for entity: {0}'.format(self._entity)
        )
        self.existingAssetSelector.loadAssets(self._entity, selectAsset=asset)
        self.existingAssetButton.setChecked(True)

    def _onAssetNameEdited(self, text):
        '''Set flag when user edits name.'''
        if text:
            self._hasEditedName = True
        else:
            self._hasEditedName = False

    def _onAssetTypeChanged(self, currentIndex):
        '''Update asset name when asset type changes, unless user has edited name.'''
        assetTypeId = self.assetTypeSelector.itemData(currentIndex)
        if not assetTypeId:
            return

        if not self._hasEditedName:
            assetType = self.session.get('AssetType', assetTypeId)
            self.assetNameLineEdit.setText(assetType['name'])

    def _toggleFieldAndLabel(self, field, toggled):
        '''Set visibility for *field* with attached label to *toggled*.'''
        if toggled:
            field._fieldLabel.show()
            field.show()
        else:
            field._fieldLabel.hide()
            field.hide()

    def _onExistingAssetToggled(self, checked):
        '''Existing asset toggled.'''
        self._toggleFieldAndLabel(self.existingAssetSelector, checked)

    def _onNewAssetToggled(self, checked):
        '''New asset toggled.'''
        self._toggleFieldAndLabel(self.assetTypeSelector, checked)
        self._toggleFieldAndLabel(self.assetNameLineEdit, checked)

    def clear(self):
        '''Clear asset option field states.'''
        self._hasEditedName = False
        self.existingAssetButton.setChecked(False)
        self.newAssetButton.setChecked(False)
        self.assetTypeSelector.selectItem(None)
        self.assetNameLineEdit.clear()
        self.existingAssetSelector.clear()

    def getState(self):
        '''Return if current state is NEW_ASSET, EXISTING_ASSET or None.'''
        state = None
        if self.existingAssetButton.isChecked():
            state = EXISTING_ASSET
        elif self.newAssetButton.isChecked():
            state = NEW_ASSET
        return state

    def getAsset(self):
        '''Return existing asset, if existing asset is selected.'''
        asset = None
        if self.getState() == EXISTING_ASSET:
            asset = self.existingAssetSelector.currentItem()
        return asset

    def getAssetType(self):
        '''Return asset type, if new asset is selected.'''
        assetType = None
        if self.getState() == NEW_ASSET:
            assetType = self.assetTypeSelector.currentItem()
        return assetType

    def getAssetName(self):
        '''Return asset name, if new asset is selected.

        ..note ::

            Raises NotUniqueError if asset name is not unique.
        '''
        assetName = None
        if self.getState() == NEW_ASSET:
            if not self.assetNameLineEdit.hasAcceptableInput():
                raise NotUniqueError('Duplicate asset name for new asset.')
            assetName = self.assetNameLineEdit.text()

        return assetName
