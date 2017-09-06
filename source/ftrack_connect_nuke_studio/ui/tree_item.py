# :coding: utf-8
# :copyright: Copyright (c) 2014 ftrack

from QtExt import QtGui, QtCore, QtWidgets
from ftrack_connect.ui.model.entity_tree import Item
from ftrack_connect.ui import resource


class TreeItem(Item):
    '''Tag Item representation for the tree.'''

    def __init__(self, entity):
        '''Initialise with *entity*.'''
        super(TreeItem, self).__init__(entity)
        self.exists = False
        self._track = None
        self._widgets = {}

    def __repr__(self):
        '''Return representation.'''
        return '<{0}:{1}>'.format(self.id, self.name)

    def __eq__(self, other):
        '''Return comparison of self and *other*.'''
        return self.__repr__() == other.__repr__()

    @property
    def track(self):
        '''Return the trackItem.'''
        return self._track

    @track.setter
    def track(self, track):
        '''Set the trackItem to *track*.'''
        self._track = track

    @property
    def icon(self):
        '''Return icon.'''
        icon = self.type

        if icon is None:
            icon = 'asset'

        elif icon == 'show':
            icon = 'home'

        icon = icon.lower()
        return QtGui.QIcon(':ftrack/image/dark/object_type/{0}'.format(icon))

    @property
    def id(self):
        '''Return id of item.'''
        return self.entity['ftrack.id']

    @property
    def name(self):
        '''Return name of item.'''
        return self.entity['tag.value']

    @property
    def type(self):
        '''Return type of item.'''
        return self.entity['ftrack.type']

    def mayHaveChildren(self):
        '''Return whether item may have children.'''
        if len(self.children) == 0:
            return False

        return True
