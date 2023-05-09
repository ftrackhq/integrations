# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack
import platform

from Qt import QtCore

import logging

from ftrack_connect_pipeline.constants import asset as asset_const


class AssetListModel(QtCore.QAbstractTableModel):
    '''Custom asset list model holding asset info data'''

    __asset_entities_list = []  # Model data storage

    @property
    def event_manager(self):
        '''Return :class:`~ftrack_connect_pipeline.event.EventManager` instance'''
        return self._event_manager

    @property
    def session(self):
        '''Return :class:`~ftrack_api.session.Session` instance'''
        return self._event_manager.session

    def __init__(self, event_manager):
        '''
        Initialize asset list model

        :param event_manager: :class:`~ftrack_connect_pipeline.event.EventManager` instance
        '''
        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )
        super(AssetListModel, self).__init__()
        self._event_manager = event_manager

    def reset(self):
        '''Empty model'''
        self.beginResetModel()
        self.__asset_entities_list = []
        self.endResetModel()

    def rowCount(self, index=QtCore.QModelIndex):
        '''Return amount of assets'''
        return len(self.__asset_entities_list)

    def columnCount(self, index=QtCore.QModelIndex):
        '''Return amount of data columns'''
        return 1

    def data(self, index, role=QtCore.Qt.DisplayRole):
        '''Return data at *index*'''
        if role == QtCore.Qt.DisplayRole:
            if index.row() < len(self.__asset_entities_list):
                return self.__asset_entities_list[index.row()]
        return None

    def items(self):
        '''Return raw data'''
        return self.__asset_entities_list

    def insertRows(self, row, data, index=None):
        '''Insert *data* at *index* (or *row* if no index defined)'''
        count = len(data)
        self.beginInsertRows(
            index or self.createIndex(row, 0), row, row + count - 1
        )
        for n in range(count):
            if row + n < len(self.__asset_entities_list):
                self.__asset_entities_list.insert(row + n, data[n])
            else:
                self.__asset_entities_list.append(data[n])
        self.endInsertRows()

    def getIndex(self, asset_info_id):
        '''Return index of asset having id provided in *asset_info_id*'''
        row = -1
        for _row, asset_info in enumerate(self.__asset_entities_list):
            if asset_info[asset_const.ASSET_INFO_ID] == asset_info_id:
                row = _row
                break
        if row == -1:
            self.logger.warning(
                'No asset info found for id {}'.format(asset_info_id)
            )
            return None
        return self.createIndex(row, 0)

    def getDataById(self, asset_info_id):
        '''Return asset info of asset having id provided in *asset_info_id*'''
        for index, asset_info in enumerate(self.__asset_entities_list):
            if asset_info[asset_const.ASSET_INFO_ID] == asset_info_id:
                return asset_info
        self.logger.warning(
            'No asset info found for id {}'.format(asset_info_id)
        )
        return None

    def setData(self, index, asset_info, silent=False, roles=None):
        '''Store the *asset_info* at *index*'''
        self.__asset_entities_list[index.row()] = asset_info
        if not silent:
            self.dataChanged.emit(index, index)

    def removeRows(self, index, count=1):
        '''Remove *count* rows starting at *index*'''
        self.beginRemoveRows(index, index.row(), count)
        for n in range(count):
            self.__asset_entities_list.pop(index.row())
        self.endRemoveRows()

    def flags(self, index):
        '''Return flags at *index*'''
        if not index.isValid():
            return QtCore.Qt.ItemIsEnabled
        return (
            QtCore.Qt.ItemFlags(QtCore.QAbstractTableModel.flags(self, index))
            | QtCore.Qt.ItemIsEditable
        )
