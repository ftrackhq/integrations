# :coding: utf-8
# :copyright: Copyright (c) 2016 ftrack

from ftrack_connect_pipeline.ui.widget.field.base import BaseField
from ftrack_connect_pipeline.ui.widget import comment

from QtExt import QtWidgets


class CommentField(BaseField):
    '''Comment field.'''

    def __init__(self):
        '''Initialize widget.'''
        super(CommentField, self).__init__()
        layout = QtWidgets.QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        self.comment = comment.Comment()
        self.layout().addWidget(self.comment)
        self.comment.textChanged.connect(self.notify_changed)

    def notify_changed(self, *args, **kwargs):
        '''Notify the world about the changes.'''
        self.value_changed.emit(self.value())

    def value(self):
        '''Return value.'''
        current_text = self.comment.toPlainText()
        return current_text
