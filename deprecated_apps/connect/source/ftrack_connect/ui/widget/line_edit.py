# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

try:
    from PySide6 import QtWidgets, QtCore, QtGui
except ImportError:
    from PySide2 import QtWidgets, QtCore, QtGui


class LineEditIconButton(QtWidgets.QToolButton):
    '''Icon button for use in a :py:class:`LineEdit` widget.'''

    iconSize = 16
    iconMargin = 4

    def __init__(self, *args, **kw):
        '''Initialise button.'''
        super(LineEditIconButton, self).__init__(*args, **kw)
        self.setCursor(QtCore.Qt.CursorShape.ArrowCursor)
        self.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)

    def paintEvent(self, event):
        '''Handle paint *event*.'''
        painter = QtGui.QPainter(self)

        # Note: isDown should ideally use the 'active' state, but in most styles
        # this has no proper feedback.
        state = QtGui.QIcon.Mode.Disabled
        if self.isEnabled():
            state = QtGui.QIcon.Mode.Normal
            if self.isDown():
                state = QtGui.QIcon.Mode.Selected

        iconPixmap = self.icon().pixmap(
            QtCore.QSize(self.iconSize, self.iconSize),
            state,
            QtGui.QIcon.State.Off,
        )

        iconRegion = QtCore.QRect(
            0, 0, iconPixmap.width(), iconPixmap.height()
        )
        iconRegion.moveCenter(self.rect().center())

        painter.drawPixmap(iconRegion, iconPixmap)


class LineEdit(QtWidgets.QLineEdit):
    '''Line edit that supports embedded actions.'''

    def __init__(self, *args, **kw):
        '''Initialise line edit.'''
        self._actionButtons = []
        self._iconSize = QtCore.QSize(
            LineEditIconButton.iconSize + 2, LineEditIconButton.iconSize + 2
        )
        self._iconRegion = QtCore.QSize(
            self._iconSize.width() + LineEditIconButton.iconMargin,
            self._iconSize.height(),
        )
        super(LineEdit, self).__init__(*args, **kw)

    def addAction(self, action):
        '''Add *action*.'''
        button = LineEditIconButton(self)
        button.setIcon(action.icon())
        button.setDefaultAction(action)
        self._actionButtons.append(button)

        currentTextMargins = self.textMargins()
        self.setTextMargins(
            currentTextMargins.left(),
            currentTextMargins.top(),
            currentTextMargins.right() + self._iconRegion.width(),
            currentTextMargins.bottom(),
        )

    def removeAction(self, action):
        '''Remove *action*.

        Raise :py:exc:`ValueError` if no matching *action* found.

        '''
        match = None
        for index, button in enumerate(self._actionButtons[:]):
            if button.defaultAction() == action:
                match = index
                break

        if match is None:
            raise ValueError('Action not found.')

        self._actionButtons[match].deleteLater()
        del self._actionButtons[match]

        currentTextMargins = self.textMargins()
        self.setTextMargins(
            currentTextMargins.left(),
            currentTextMargins.top(),
            currentTextMargins.right() - self._iconRegion.width(),
            currentTextMargins.bottom(),
        )

    def resizeEvent(self, event):
        '''Handle resize *event*.

        Position action buttons.

        '''
        contentRegion = self.rect()

        widgetGeometry = QtCore.QRect(
            QtCore.QPoint(
                contentRegion.width() - self._iconRegion.width(),
                (contentRegion.height() - self._iconRegion.height()) / 2,
            ),
            self._iconSize,
        )

        for button in self._actionButtons:
            button.setGeometry(widgetGeometry)
            widgetGeometry.moveLeft(
                widgetGeometry.left() - self._iconRegion.width()
            )
