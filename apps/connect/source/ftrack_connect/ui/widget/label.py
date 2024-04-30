# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

try:
    from PySide6 import QtWidgets, QtCore, QtGui
except ImportError:
    from PySide2 import QtWidgets, QtCore, QtGui


class Label(QtWidgets.QLabel):
    '''Label that can elide displayed text automatically.'''

    def __init__(
        self, elideMode=QtCore.Qt.TextElideMode.ElideMiddle, *args, **kwargs
    ):
        '''Instantiate label with *elideMode*.

        If *elideMode* is not specified it defaults to
        :py:class:`QtCore.Qt.ElideMiddle.`

        '''
        self.elideMode = elideMode
        super(Label, self).__init__(*args, **kwargs)

        # Set low horizontal minimum size so that the label can shrink and make
        # use of eliding. Note the label will still try to take as much
        # horizontal space as possible.
        self.setMinimumWidth(25)

    def paintEvent(self, event):
        '''Paint *event* with the configured elideMode.'''
        painter = QtGui.QPainter(self)

        metrics = QtGui.QFontMetrics(self.font())
        elided = metrics.elidedText(self.text(), self.elideMode, self.width())

        painter.drawText(self.rect(), self.alignment(), elided)
