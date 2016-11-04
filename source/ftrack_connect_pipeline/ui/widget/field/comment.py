# :coding: utf-8
# :copyright: Copyright (c) 2014 ftrack

from .base import BaseField

from QtExt import QtCore, QtWidgets


class CommentField(BaseField):
    '''Create new comment.'''

    def __init__(self):
        super(CommentField, self).__init__()
        main_layout = QtWidgets.QVBoxLayout()
        self.setLayout(main_layout)
        main_layout.setContentsMargins(0,0,0,0)

        group_box = QtWidgets.QGroupBox("Comment")
        box_layout = QtWidgets.QVBoxLayout()
        group_box.setLayout(box_layout)

        self.comment = QtWidgets.QTextEdit()

        main_layout.addWidget(group_box)
        box_layout.addWidget(self.comment)

        self.comment.textChanged.connect(self.notify_changed)

    def notify_changed(self, *args, **kwargs):
        '''Notify the world about the changes.'''
        self.value_changed.emit(self.value())

    def value(self):
        '''Return value.'''
        return {
            'comment': self.comment.toPlainText()
        }
