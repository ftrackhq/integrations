# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import logging

from Qt import QtWidgets, QtCore


class VersionSelector(QtWidgets.QComboBox):
    '''Version selector combobox'''

    @property
    def version(self):
        '''Return current selected asset version entity'''
        index = self.currentIndex()
        if index > -1:
            return self.itemData(index)
        else:
            return None

    def __init__(self, parent=None):
        super(VersionSelector, self).__init__(parent=parent)
        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )

        self.setEditable(False)

        self.setMaximumHeight(24)
        self.setMinimumHeight(24)

    def set_versions(self, versions):
        self.clear()
        self._add_versions(sorted(versions, key=lambda v: -v['version']))

    def _add_versions(self, sorted_versions):
        '''Add *versions* list of assetversion entities to the combobox'''
        for index, version in enumerate(sorted_versions):
            self._add_version(version)
        self.setCurrentIndex(0)

    def _add_version(self, version):
        '''Add *version* assetversion entity to the combobox'''
        self.addItem(str('v{}'.format(version['version'])), version)
