# :coding: utf-8
# :copyright: Copyright (c) 2014 ftrack
#             Copyright (c) 2014 Martin Pengelly-Phillips
# :notice: Derived from Riffle (https://gitlab.com/4degrees/riffle)

from QtExt import QtWidgets, QtCore, QtGui

from ftrack_connect_pipeline import util


def ItemFactory(session, entity):
    '''Return appropriate :py:class:`Item` to represent *entity*.

    If *entity* is null then return :class:`Root` item.

    '''
    if not entity:
        return Root(session)

    return Context(session, entity)


class Item(object):
    '''Represent ftrack entity with consistent interface.'''

    def __init__(self, entity):
        '''Initialise item with *entity*.'''
        super(Item, self).__init__()
        self.entity = entity

        self.children = []
        self.parent = None
        self._fetched = False

    def __repr__(self):
        '''Return representation.'''
        return '<{0} {1}>'.format(self.__class__.__name__, self.entity)

    @property
    def id(self):
        '''Return id of item.'''
        return self.entity.get('id')

    @property
    def name(self):
        '''Return name of item.'''
        return self.entity.get('name')

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
        return []

    def clearChildren(self):
        '''Remove all children and return to un-fetched state.'''
        # Reset children
        for child in self.children[:]:
            self.removeChild(child)

        # Enable children fetching
        self._fetched = False


class Root(Item):
    '''Represent root.'''

    def __init__(self, session):
        '''Initialise item.'''
        self._session = session
        super(Root, self).__init__(None)

    @property
    def name(self):
        '''Return name of item.'''
        return 'ftrack'

    @property
    def type(self):
        '''Return type of item as string.'''
        return 'Root'

    def _fetchChildren(self):
        '''Fetch and return new child items.'''
        children = []
        for entity in self._session.query('Project where status is active'):
            children.append(Project(self._session, entity))

        return children


class Context(Item):
    '''Represent context entity.'''

    def __init__(self, session, entity):
        '''Initialise item.'''
        self._session = session
        super(Context, self).__init__(entity)

    @property
    def type(self):
        '''Return type of item as string.'''
        return self.entity.get('object_type', {}).get('name')

    @property
    def icon(self):
        '''Return icon.'''
        icon = self.entity.get('object_type', {}).get('icon', 'default')
        return QtGui.QIcon(
            ':/ftrack/image/light/object_type/{0}'.format(icon)
        )

    def _fetchChildren(self):
        '''Fetch and return new child items.'''
        children = []
        entities = self._session.query(
            (
                'select name, object_type_id, object_type.name, '
                'object_type.is_leaf, object_type.icon from TypedContext '
                'where parent_id is {0}'
            ).format(self.entity['id'])
        )
        for entity in entities:
            children.append(ItemFactory(self._session, entity))

        return children

    def mayHaveChildren(self):
        '''Return whether item may have children.'''
        return self.entity.get('object_type', {}).get('is_leaf') != True


class Project(Context):
    '''Represent project entity.'''

    @property
    def type(self):
        '''Return type of item as string.'''
        return 'Project'

    @property
    def icon(self):
        '''Return icon.'''
        return QtGui.QIcon(':/ftrack/image/light/project')


class EntityTreeModel(QtCore.QAbstractItemModel):
    '''Model representing entity tree.'''

    #: Role referring to :class:`Item` instance.
    ITEM_ROLE = QtCore.Qt.UserRole + 1

    #: Role referring to the unique identity of :class:`Item`.
    IDENTITY_ROLE = ITEM_ROLE + 1

    #: Signal that a loading operation has started.
    loadStarted = QtCore.Signal()

    #: Signal that a loading operation has ended.
    loadEnded = QtCore.Signal()

    def __init__(self, root=None, parent=None):
        '''Initialise with *root* entity and optional *parent*.'''
        super(EntityTreeModel, self).__init__(parent=parent)
        self.root = root
        self.columns = ['Name', 'Type']

    def rowCount(self, parent):
        '''Return number of children *parent* index has.'''
        if parent.column() > 0:
            return 0

        if parent.isValid():
            item = parent.internalPointer()
        else:
            item = self.root

        return len(item.children)

    def columnCount(self, parent):
        '''Return amount of data *parent* index has.'''
        return len(self.columns)

    def flags(self, index):
        '''Return flags for *index*.'''
        if not index.isValid():
            return QtCore.Qt.NoItemFlags

        return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

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

    def match(self, *args, **kwargs):
        return super(EntityTreeModel, self).match(*args, **kwargs)

    def item(self, index):
        '''Return item at *index*.'''
        return self.data(index, role=self.ITEM_ROLE)

    def icon(self, index):
        '''Return icon for index.'''
        return self.data(index, role=QtCore.Qt.DecorationRole)

    def data(self, index, role):
        '''Return data for *index* according to *role*.'''
        if not index.isValid():
            return None

        column = index.column()
        item = index.internalPointer()

        if role == self.ITEM_ROLE:
            return item

        elif role == self.IDENTITY_ROLE:
            return item.id

        elif role == QtCore.Qt.DisplayRole:
            column_name = self.columns[column]

            if column_name == 'Name':
                return item.name
            elif column_name == 'Type':
                return item.type

        elif role == QtCore.Qt.DecorationRole:
            if column == 0:
                return item.icon

        return None

    def headerData(self, section, orientation, role):
        '''Return label for *section* according to *orientation* and *role*.'''
        if orientation == QtCore.Qt.Horizontal:
            if section < len(self.columns):
                column = self.columns[section]
                if role == QtCore.Qt.DisplayRole:
                    return column

        return None

    def hasChildren(self, index):
        '''Return if *index* has children.

        Optimised to avoid loading children at this stage.

        '''
        if not index.isValid():
            item = self.root
        else:
            item = index.internalPointer()
            if not item:
                return False

        return item.mayHaveChildren()

    def canFetchMore(self, index):
        '''Return if more data available for *index*.'''
        if not index.isValid():
            item = self.root
        else:
            item = index.internalPointer()

        return item.canFetchMore()

    def fetchMore(self, index):
        '''Fetch additional data under *index*.

        Loading is done in a background thread with UI events continually
        processed to maintain a responsive interface.

        :attr:`EntityTreeModel.loadStarted` is emitted at start of load with
        :attr:`EntityTreeModel.loadEnded` emitted when load completes.

        '''
        if not index.isValid():
            item = self.root
        else:
            item = index.internalPointer()

        if item.canFetchMore():
            self.loadStarted.emit()
            startIndex = len(item.children)

            worker = util.Worker(item.fetchChildren)
            worker.start()

            while worker.isRunning():
                app = QtWidgets.QApplication.instance()
                app.processEvents()

            if worker.error:
                raise worker.error[1], None, worker.error[2]

            additionalChildren = worker.result

            endIndex = startIndex + len(additionalChildren) - 1
            if endIndex >= startIndex:
                self.beginInsertRows(index, startIndex, endIndex)
                for newChild in additionalChildren:
                    item.addChild(newChild)
                self.endInsertRows()

            self.loadEnded.emit()

    def reloadChildren(self, index):
        '''Reload the children of parent *index*.'''
        if not self.hasChildren(index):
            return

        if not index.isValid():
            item = self.root
        else:
            item = index.internalPointer()

        self.beginRemoveRows(index, 0, self.rowCount(index))
        item.clearChildren()
        self.endRemoveRows()

    def reset(self):
        '''Reset model'''
        self.beginResetModel()
        self.root.clearChildren()
        self.endResetModel()


class EntityTreeProxyModel(QtCore.QSortFilterProxyModel):
    '''Sort contexts before tasks.'''

    def lessThan(self, left, right):
        '''Return ordering of *left* vs *right*.'''
        sourceModel = self.sourceModel()
        if sourceModel:
            leftItem = sourceModel.item(left)
            rightItem = sourceModel.item(right)

            if (
                isinstance(leftItem, (Context, Project))
                and not isinstance(rightItem, (Context, Project))
            ):
                return self.sortOrder() == QtCore.Qt.AscendingOrder

            elif (
                not isinstance(leftItem, (Context, Project))
                and isinstance(rightItem, (Context, Project))
            ):
                return self.sortOrder() == QtCore.Qt.DescendingOrder

        return super(EntityTreeProxyModel, self).lessThan(left, right)

    @property
    def root(self):
        '''Return root of model.'''
        sourceModel = self.sourceModel()
        if not sourceModel:
            return None

        return sourceModel.root

    def hasChildren(self, index):
        '''Return if *index* has children.'''
        sourceModel = self.sourceModel()

        if not sourceModel:
            return False

        return sourceModel.hasChildren(self.mapToSource(index))

    def reloadChildren(self, index):
        '''Reload the children of parent *index*.'''
        sourceModel = self.sourceModel()

        if not sourceModel:
            return False

        return sourceModel.reloadChildren(self.mapToSource(index))

    def match(self, start, *args, **kwargs):
        sourceModel = self.sourceModel()

        if not sourceModel:
            return []

        matches = sourceModel.match(self.mapToSource(start), *args, **kwargs)
        return map(self.mapFromSource, matches)

    def item(self, index):
        '''Return item at *index*.'''
        sourceModel = self.sourceModel()

        if not sourceModel:
            return None

        return sourceModel.item(self.mapToSource(index))

    def icon(self, index):
        '''Return icon for index.'''
        sourceModel = self.sourceModel()
        if not sourceModel:
            return None

        return sourceModel.icon(self.mapToSource(index))
