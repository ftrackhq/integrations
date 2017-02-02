# :coding: utf-8
# :copyright: Copyright (c) 2016 ftrack

from QtExt import QtWidgets


class Comment(QtWidgets.QTextEdit):
    def __init__(self, parent=None):
        super(Comment, self).__init__(parent=parent)
        self._placeholder_text = 'Please add a comment...'
        self._set_placeholder_text(self._placeholder_text)

    def _set_placeholder_text(self, text):
        self.setHtml('<font color="#808080">{0}</font>'.format(text))

    def focusInEvent(self, event):
        current_text = self.toPlainText()
        if not current_text or current_text == self._placeholder_text:
            self.clear()
        super(Comment, self).focusInEvent(event)

    def focusOutEvent(self, event):
        current_text = self.toPlainText()
        if not current_text:
            self._set_placeholder_text(self._placeholder_text)
        super(Comment, self).focusOutEvent(event)
