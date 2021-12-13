# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

from Qt import QtWidgets, QtCore, QtGui

from ftrack_connect_pipeline.asset import asset_info
from ftrack_connect_pipeline_qt.constants import asset as asset_constants
from ftrack_connect_pipeline.constants import asset as core_asset_constants

class Item(object):
    '''Represent ftrack entity with consistent interface.'''

    def __init__(self, asset_info):
        '''Initialise item with *entity*.
        asset_info: {'asset_id': 'db4ad014-5b76-434b-8a0f-ab6ae979ef4d', 'asset_name': 'uploadasset',
            'asset_type_name': 'Upload', 'version_id': '1720f6f3-4854-4796-a2ce-fe225178bf49', 'version_number': 2,
            'component_path': '/Volumes/AccsynStorage/accsynftrackpoc/sq010/sh030/_PUBLISH/generic/v002/main.mp4',
            'component_name': 'main', 'component_id': 'a07e3c4a-8f51-4492-bc97-04a54cf94fbb', 'load_mode': None,
            'asset_info_options': None, 'reference_object': None, 'is_latest_version': True,
            'asset_versions_entities': None, 'session': <ftrack_api.session.Session object at 0x102975210>,
            'asset_info_id': '51b6abdc3c5141a3bbe79983c5a2813f', 'dependency_ids': [], 'is_dependency': False,
             'dependencies': None, 'context_name': 'sh030'}
        '''
        super(Item, self).__init__()
        self.asset_info = asset_info
        self.children = []
        self.parent = None
        self._fetched = False

    def __repr__(self):
        '''Return representation.'''
        return '<{0} {1}>'.format(self.__class__.__name__, self.asset_info)

    # @property
    # def name(self):
    #     '''Return name of item.'''
    #     return self.asset_info.get('name')

    @property
    def type(self):
        '''Return type of item as string.'''
        return ''

    @property
    def icon(self):
        '''Return icon.'''
        return QtGui.QIcon(':/ftrack/image/default/ftrackLogoGreyDark')

    @property
    def row(self):
        '''Return index of this item in its parent or 0 if no parent.'''
        if self.parent:
            return self.parent.children.index(self)

        return 0

    def addChild(self, item):
        '''Add *item* as child of this item.

        .. note::

            If *item* is already a child of this item then return without
            making any modifications.

        '''
        if item.parent:
            if item.parent == self:
                return

            item.parent.removeChild(item)

        self.children.append(item)
        item.parent = self

    def addChildren(self, items):
        '''Add *item* as child of this item.

        .. note::

            If *item* is already a child of this item then return without
            making any modifications.

        '''
        for item in items:
            self.addChild(item)

    def removeChild(self, item):
        '''Remove *item* from children.'''
        item.parent = None
        self.children.remove(item)

    def canFetchMore(self):
        '''Return whether more items can be fetched under this one.'''
        if not self._fetched:
            if self.mayHaveChildren():
                return True

        return False

    def mayHaveChildren(self):
        '''Return whether item may have children.'''
        return True

    def fetchChildren(self):
        '''Fetch and return new children.

        Will only fetch children whilst canFetchMore is True.

        .. note::

            It is the caller's responsibility to add each fetched child to this
            parent if desired using :py:meth:`Item.addChild`.

        '''
        if not self.canFetchMore():
            return []

        self._fetched = True
        children = self._fetchChildren()

        return children

    def _fetchChildren(self):
        '''Fetch and return new child items.

        Override in subclasses to fetch actual children and return list of
        *unparented* :py:class:`Item` instances.

        '''
        self.asset_info.update_dependencies()
        children = []
        for dependency in self.asset_info.get(core_asset_constants.DEPENDENCIES, []):
            #TODO: if we want more than one level of depth in dependencies,
            # call fetch childen before append the item
            item = Item(dependency)
            children.append(item)
        return children

    def clearChildren(self):
        '''Remove all children and return to un-fetched state.'''
        # Reset children
        for child in self.children[:]:
            self.removeChild(child)

        # Enable children fetching
        self._fetched = False


class AssetManagerModel(QtCore.QAbstractItemModel):
    '''Model representing AssetManager.'''

    DATA_ROLE = QtCore.Qt.UserRole + 1

    @property
    def root(self):
        '''
        Returns the :obj:`_root`
        '''
        return self._root

    def __init__(self, asset_entities_list=None, parent=None):
        '''Initialise Model.'''
        super(AssetManagerModel, self).__init__(parent=parent)
        asset_entities_list = asset_entities_list or []
        self._root = Item(None)
        if asset_entities_list:
            self.set_asset_list(asset_entities_list)

        self.columns = asset_constants.KEYS

    def set_asset_list(self, asset_entities_list):
        '''
        Reset the model and sets the :obj:`asset_entities_list` with the given
        *asset_entities_list*
        '''
        self.beginResetModel()
        for asset_entity in asset_entities_list:
            new_item = Item(asset_entity)
            self._root.addChild(new_item)
            children = new_item.fetchChildren()
            new_item.addChildren(children)
        self.endResetModel()

    def index(self, row, column, parent=None):
        '''Return index for *row* and *column* under *parent*.'''
        if parent is None:
            parent = QtCore.QModelIndex()

        if not self.hasIndex(row, column, parent):
            return QtCore.QModelIndex()

        if not parent.isValid():
            item = self.root
        else:
            item = parent.internalPointer()

        try:
            child = item.children[row]
        except IndexError:
            return QtCore.QModelIndex()
        else:
            return self.createIndex(row, column, child)

    def parent(self, index):
        '''Return parent of *index*.'''
        if not index.isValid():
            return QtCore.QModelIndex()

        item = index.internalPointer()
        if not item:
            return QtCore.QModelIndex()

        parent = item.parent
        if not parent or parent == self.root:
            return QtCore.QModelIndex()

        return self.createIndex(parent.row, 0, parent)

    def rowCount(self, parent=QtCore.QModelIndex()):
        '''Return the row count for the internal data.'''
        if parent.column() > 0:
            return 0

        if parent.isValid():
            item = parent.internalPointer()
        else:
            item = self.root

        return len(item.children)

    def columnCount(self, parent=QtCore.QModelIndex()):
        '''Return the column count for the internal data.'''
        return len(self.columns)

    # def removeRows(self, position, rows=1, index=QtCore.QModelIndex()):
    #     '''
    #     Removes the row in the given *position*
    #     '''
    #     self.beginRemoveRows(index, position, position + rows - 1)
    #
    #     self.root.pop(position)
    #
    #     self.endRemoveRows()
    #     return True

    def data(self, index, role=QtCore.Qt.DisplayRole):
        '''Return the data provided in the given *index* and with *role*'''
        if not index.isValid():
            return None

        column = index.column()
        item = index.internalPointer()


        data = item.asset_info.get(self.columns[column])

        # style versions
        if (
                role == QtCore.Qt.BackgroundRole and
                index.column() == self.get_version_column_index()
        ):
            if item.asset_info.get(core_asset_constants.IS_LATEST_VERSION):#.is_latest:
                return QtGui.QBrush(QtGui.QColor(155, 250, 218, 200))
            else:
                return QtGui.QBrush(QtGui.QColor(250, 171, 155, 200))

        elif (
                role == QtCore.Qt.TextAlignmentRole and
                index.column() == self.get_version_column_index()
        ):
            return QtCore.Qt.AlignCenter

        elif (role == QtCore.Qt.TextColorRole and
              index.column() == self.get_version_column_index()
        ):
            return QtGui.QColor(0, 0, 0, 255)

        # style the rest
        elif role == QtCore.Qt.DisplayRole:
            return data

        elif role == QtCore.Qt.EditRole:
            return data

        elif role == self.DATA_ROLE:
            return item.asset_info

        return None

    def headerData(self, column, orientation, role):
        '''Provide header data'''
        if (
                orientation == QtCore.Qt.Horizontal and
                role == QtCore.Qt.DisplayRole
        ):
            return self.columns[column].replace('_', ' ').capitalize()

        return None

    def setData(self, index, value, role=QtCore.Qt.EditRole):
        '''
        Sets the givn *value* to the given *index*
        '''
        if role == QtCore.Qt.EditRole:
            if value:
                self.dataChanged.emit(index, index)
                return True
            return False
        else:
            return super(AssetManagerModel, self).setData(index, value, role)

    def flags(self, index):
        if index.column() == self.get_version_column_index():
            return QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled
        else:
            return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

    def get_version_column_index(self):
        '''Returns the column index of the version_number column'''
        return self.columns.index(core_asset_constants.VERSION_NUMBER)

    def set_host_connection(self, host_connection):
        '''Sets the host connection'''
        self.host_connection = host_connection

    def reset(self):
        '''Reset model'''
        self.beginResetModel()
        self.root.clearChildren()
        self.endResetModel()


class FilterProxyModel(QtCore.QSortFilterProxyModel):

    DATA_ROLE = AssetManagerModel.DATA_ROLE

    @property
    def asset_entities_list(self):
        return self.sourceModel().asset_entities_list

    def __init__(self, parent=None):
        '''Initialize the FilterProxyModel'''
        super(FilterProxyModel, self).__init__(parent=parent)

        self.setDynamicSortFilter(True)
        self.setFilterCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self.setFilterKeyColumn(-1)

    def filterAcceptsRowItself(self, source_row, source_parent):
        '''Provide a way to filter internal values.'''
        return super(FilterProxyModel, self).filterAcceptsRow(
            source_row, source_parent
        )

    def filterAcceptsRow(self, source_row, source_parent):
        '''Override filterAcceptRow to filter to any entry.'''
        if self.filterAcceptsRowItself(source_row, source_parent):
            return True

        parent = source_parent
        while parent.isValid():
            if self.filterAcceptsRowItself(parent.row(), parent.parent()):
                return True
            parent = parent.parent()

        return False

    def lessThan(self, left, right):
        '''Allow to sort the model.'''
        left_data = self.sourceModel().item(left)
        right_data = self.sourceModel().item(right)
        print((left_data, right_data))
        return left_data.id > right_data.id

