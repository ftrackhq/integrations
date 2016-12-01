# :coding: utf-8
# :copyright: Copyright (c) 2016 ftrack

from .base import BaseField
from QtExt import QtWidgets


class AssetSelector(BaseField):
    '''Select or create a new asset.'''

    def __init__(self, ftrack_entity, hint=None):
        '''Instantiate asset selector with *ftrack_entity*.'''
        super(AssetSelector, self).__init__()

        self.assets = ftrack_entity.session.query(
            'select name, id, type_id from Asset where context_id '
            'is "{0}"'.format(
                ftrack_entity['id']
            )
        ).all()

        main_layout = QtWidgets.QVBoxLayout(self)
        self.setLayout(main_layout)
        main_layout.setContentsMargins(0, 0, 0, 0)

        self.asset_selector = QtWidgets.QComboBox(self)
        main_layout.addWidget(self.asset_selector)

        self.asset_selector.addItem('Create new asset')
        for asset in self.assets:
            self.asset_selector.addItem(asset['name'])

        self.asset_name = QtWidgets.QLineEdit(self)
        self.asset_name.setPlaceholderText('Asset name...')
        main_layout.addWidget(self.asset_name)

        self.asset_type_selector = QtWidgets.QComboBox(self)

        self.asset_types = ftrack_entity.session.query(
            'select name, short, id from AssetType'
        ).all()

        for asset_type in self.asset_types:
            self.asset_type_selector.addItem(asset_type['name'])

        # automatically set the correct asset type
        if hint:
            for index, asset_type in enumerate(self.asset_types):
                if asset_type['short'] == hint:
                    self.asset_type_selector.setCurrentIndex(index)
                    break

        main_layout.addWidget(self.asset_type_selector)

        self.asset_selector.currentIndexChanged.connect(
            self._on_asset_selection_changed
        )
        self.asset_type_selector.currentIndexChanged.connect(
            self.notify_changed
        )
        self.asset_name.textChanged.connect(self.notify_changed)

    def _on_asset_selection_changed(self, index):
        if index != 0:
            self.asset_name.hide()
            self.asset_type_selector.hide()
        else:
            self.asset_name.show()
            self.asset_type_selector.show()

        self.notify_changed()

    def notify_changed(self, *args, **kwargs):
        '''Notify the world about the changes.'''
        self.value_changed.emit(self.value())

    def value(self):
        '''Return value.'''
        index = self.asset_selector.currentIndex()
        if index == 0:
            return {
                'asset_name': self.asset_name.text(),
                'asset_type': (
                    self.asset_types[self.asset_type_selector.currentIndex()]['id']
                )
            }

        return {
            'asset_name': self.assets[index - 1]['name'],
            'asset_type': self.assets[index - 1]['type_id'],
        }
