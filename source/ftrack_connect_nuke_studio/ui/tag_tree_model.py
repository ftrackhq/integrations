# :coding: utf-8
# :copyright: Copyright (c) 2014 ftrack

import logging

from QtExt import QtGui, QtCore, QtWidgets

from ftrack_connect.ui.model.entity_tree import EntityTreeModel
from ftrack_connect_nuke_studio.ui.helper import (
    time_from_track_item, timecode_from_track_item, source_from_track_item
)


class TagTreeModel(EntityTreeModel):
    ''' A morel representing the hierarchy tree of the context.'''

    project_exists = QtCore.Signal(str)

    def __init__(self, tree_data=None, parent=None):
        '''Define a new TagTreeModel with *tree_data* and *parent*.

        TagTreeModel represents the context structure defined by ftags items.

        '''
        super(TagTreeModel, self).__init__(parent=parent)
        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )

        self.root = tree_data
        self.columns = [
            'Name',
            'Start',
            'End',
            'Duration',
            'Tc src In',
            'Tc src Out',
            'Tc dst In',
            'Tc dst Out',
            'Source',
            'Type']

        self.parentWidget = parent

    def setRoot(self, root):
        ''' Set the root of the tree.'''
        self.beginResetModel()
        self.root = root
        self.endResetModel()

    def data(self, index, role):
        ''' Set the data of the model for the given index and role.'''
        item = index.internalPointer()
        column = index.column()

        if role == QtCore.Qt.DisplayRole:
            column_name = self.columns[column]

            if column_name == 'Name':
                return item.name

            elif column_name == 'Type':
                return item.type

            if item.type == 'show' and item.exists:
                self.project_exists.emit(item.name)

            if item.type == 'shot':
                start, end, in_, out = time_from_track_item(
                    item.track, self.parentWidget
                )
                in_src, out_src, in_dst, out_dst = timecode_from_track_item(
                    item.track
                )
                source = source_from_track_item(item.track)

                if column_name == 'Start':
                    return start

                if column_name == 'End':
                    return end

                if column_name == 'Duration':
                    return end - start

                if column_name == 'Tc src In':
                    return in_src

                if column_name == 'Tc src Out':
                    return out_src

                if column_name == 'Tc dst In':
                    return in_dst

                if column_name == 'Tc dst Out':
                    return out_dst

                if column_name == 'Source':
                    return source

        elif role == QtCore.Qt.ForegroundRole:
            if item.exists == 'error':
                return QtGui.QColor('orange')

            elif item.exists:
                return QtGui.QColor('#278F74')

            else:
                return QtGui.QColor('white')

        elif role == QtCore.Qt.TextAlignmentRole:
                return QtCore.Qt.AlignLeft

        else:
            return super(TagTreeModel, self).data(index, role)
