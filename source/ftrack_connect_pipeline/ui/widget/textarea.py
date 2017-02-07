# :coding: utf-8
# :copyright: Copyright (c) 2017 ftrack

from QtExt import QtWidgets


class TextArea(QtWidgets.QTextEdit):
    '''Text area with placeholder.'''

    def __init__(self, placeholder_text, parent=None):
        '''Instantiate text area.'''
        super(TextArea, self).__init__(parent=parent)
        self._placeholder_text = placeholder_text
        self.set_placeholder_text(self._placeholder_text)

    def set_placeholder_text(self, text):
        '''Set placeholder text to *text*.'''
        self._placeholder_text = text
        self.setHtml('<font color="#808080">{0}</font>'.format(text))

    def focusInEvent(self, event):
        '''Handle In Focus *event*.'''
        current_text = self.toPlainText()
        if not current_text or current_text == self._placeholder_text:
            self.clear()
        super(TextArea, self).focusInEvent(event)

    def focusOutEvent(self, event):
        '''Handle In Focus *event*.'''
        current_text = self.toPlainText()
        if not current_text:
            self.set_placeholder_text(self._placeholder_text)
        super(TextArea, self).focusOutEvent(event)
