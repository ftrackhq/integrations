# :coding: utf-8
# :copyright: Copyright (c) 2014 ftrack

from FnAssetAPI.ui.toolkit import QtGui
from ftrack_connect.ui.model.entity_tree import Item


class TagItem(Item):
    '''Tag Item representation for the tree.
    '''
    def __init__(self, entity):
        super(TagItem, self).__init__(entity)
        self.exists = False
        self._track = None
        self._widgets = {}

    def __repr__(self):
        return '<%s:%s>' % (self.id, self.name)

    def __eq__(self, other):
        return self.__repr__() == other.__repr__()

    @property
    def track(self):
        ''' Return the trackItem.
        '''
        return self._track

    @track.setter
    def track(self, track):
        ''' Set the trackItem.
        '''
        self._track = track

    @property
    def icon(self):
        '''Return icon.
        '''
        icon = self.type

        if icon is None:
            icon = 'asset'

        elif icon == 'show':
            icon = 'home'

        elif icon not in ('episode', 'shot', 'task'):
            icon = 'folder'

        icon = icon.lower()
        return QtGui.QIcon(':/ftrack/image/dark/{0}'.format(icon))

    @property
    def id(self):
        '''Return id of item.
        '''
        return self.entity['ftrack.id']

    @property
    def name(self):
        '''Return name of item.
        '''
        return self.entity['tag.value']

    @property
    def type(self):
        '''Return type of item.
        '''
        return self.entity['ftrack.type']

    def mayHaveChildren(self):
        '''Return whether item may have children.
        '''
        if len(self.children) == 0:
            return False

        return True