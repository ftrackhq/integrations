# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from Qt import QtGui, QtCore, QtWidgets

import ftrack_connect.ui.widget.entity_browser as _entity_browser
import ftrack_connect.ui.widget.entity_path as _entity_path
import ftrack_connect.ui.widget.asset_options as _asset_options
from harness import Harness

TASK_ID = '9e9b2100-5910-11e4-8a3c-3c0754282242'


class WidgetHarness(Harness):
    '''Test harness for widget.'''

    def constructWidget(self):
        '''Return widget instance to test.'''
        widget = QtWidgets.QWidget()
        formLayout = QtWidgets.QFormLayout()
        widget.setLayout(formLayout)

        self.entityField = QtWidgets.QLineEdit(TASK_ID)
        formLayout.addRow('Task ID:', self.entityField)
        updateEntityButton = QtWidgets.QPushButton('Update entity')
        updateEntityButton.clicked.connect(self.updateEntity)
        formLayout.addRow(updateEntityButton)

        self.assetOptions = _asset_options.AssetOptions(self.session)
        formLayout.addRow('Asset', self.assetOptions.radioButtonFrame)
        formLayout.addRow(
            'Existing asset', self.assetOptions.existingAssetSelector
        )
        formLayout.addRow('Type', self.assetOptions.assetTypeSelector)
        formLayout.addRow('Name', self.assetOptions.assetNameLineEdit)
        self.assetOptions.initializeFieldLabels(formLayout)

        return widget

    def updateEntity(self):
        try:
            entity = self.session.get('Task', self.entityField.text())
        except Exception:
            entity = None

        self.setEntity(entity)

    def setEntity(self, entity):
        '''Set the *entity* for the view.'''
        self.assetOptions.setEntity(entity)


if __name__ == '__main__':
    raise SystemExit(WidgetHarness().run())
