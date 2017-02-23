# :coding: utf-8
# :copyright: Copyright (c) 2017 ftrack

from ftrack_connect_pipeline.ui.widget.field.base import BaseField
from ftrack_connect_pipeline.ui.widget import textarea

from QtExt import QtWidgets


class TextAreaField(BaseField):
    '''Textarea field.'''

    def __init__(self, placeholder):
        '''Initialize widget.'''
        super(TextAreaField, self).__init__()
        layout = QtWidgets.QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        self.textarea = textarea.TextArea(placeholder)
        self.layout().addWidget(self.textarea)
        self.textarea.textChanged.connect(self.notify_changed)

    def notify_changed(self, *args, **kwargs):
        '''Notify the world about the changes.'''
        self.value_changed.emit(self.value())

    def value(self):
        '''Return value.'''
        current_text = self.textarea.toPlainText()
        return current_text
