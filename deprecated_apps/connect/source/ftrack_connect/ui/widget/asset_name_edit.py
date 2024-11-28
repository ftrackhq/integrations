# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

try:
    from PySide6 import QtWidgets, QtGui
except ImportError:
    from PySide2 import QtWidgets, QtGui


class AssetNameValidator(QtGui.QValidator):
    '''Asset Name Validator.

    Validates the input's uniqueness using *assetSelector* and
    *assetTypeSelector*.
    '''

    @property
    def session(self):
        '''Return current session.'''
        return self._session

    def __init__(self, session, assetSelector, assetTypeSelector, **kwargs):
        self._session = session
        self.assetSelector = assetSelector
        self.assetTypeSelector = assetTypeSelector
        super(AssetNameValidator, self).__init__(**kwargs)

    def fixup(self, value):
        return value

    def validate(self, value, position):
        assetTypeId = self.assetTypeSelector.currentItem()
        isValid = True
        for asset_id in self.assetSelector.items():
            asset = self.session.get('Asset', asset_id)
            if (
                asset['type']['id'] == assetTypeId
                and asset['name'].lower() == value.lower()
            ):
                isValid = False
                break

        if not value or not isValid:
            return QtGui.QValidator.State.Intermediate
        else:
            return QtGui.QValidator.State.Acceptable


class AssetNameEdit(QtWidgets.QLineEdit):
    '''Asset Name line edit

    ..note ::

        Validates the input's uniqueness using *assetSelector* and
        *assetTypeSelector*.
    '''

    def __init__(self, session, assetSelector, assetTypeSelector, **kwargs):
        super(AssetNameEdit, self).__init__(**kwargs)
        self.setValidator(
            AssetNameValidator(session, assetSelector, assetTypeSelector)
        )
