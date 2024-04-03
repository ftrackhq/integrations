# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import logging

try:
    from PySide6 import QtWidgets, QtCore, QtGui
except ImportError:
    from PySide2 import QtWidgets, QtCore, QtGui

import ftrack_connect.ui.widget.indicator

logger = logging.getLogger(__name__)


class Overlay(QtWidgets.QFrame):
    '''Display a transparent overlay over another widget.

    Customise the background colour using stylesheets. The widget has an object
    name of "overlay".

    While the overlay is active, the target widget and its children will not
    receive interaction events from the user (e.g. focus).

    '''

    def __init__(self, parent):
        '''Initialise overlay for target *parent*.'''
        super(Overlay, self).__init__(parent=parent)
        self.setObjectName('overlay')
        self.setFrameStyle(
            QtWidgets.QFrame.Shape.StyledPanel | QtWidgets.QFrame.Shadow.Plain
        )

        self._event_filter_installed = False

    def __del__(self):
        if self._event_filter_installed:
            application = QtCore.QCoreApplication.instance()
            application.removeEventFilter(self)

    def setVisible(self, visible):
        '''Set whether *visible* or not.'''
        if visible:
            if not self._event_filter_installed:
                # Install global event filter that will deal with matching parent size
                # and disabling parent interaction when overlay is visible.
                application = QtCore.QCoreApplication.instance()
                application.installEventFilter(self)
                self._event_filter_installed = True
            # Manually clear focus from any widget that is overlaid. This
            # works in conjunction with :py:meth`eventFilter` to prevent
            # interaction with overlaid widgets.
            parent = self.parent()
            if parent.hasFocus():
                parent.clearFocus()
            else:
                for widget in parent.findChildren(QtWidgets.QWidget):
                    if self.isAncestorOf(widget):
                        # Ignore widgets that are part of the overlay.
                        continue

                    if widget.hasFocus():
                        widget.clearFocus()
                        break
        else:
            if self._event_filter_installed:
                application = QtCore.QCoreApplication.instance()
                application.removeEventFilter(self)
                self._event_filter_installed = False
        super(Overlay, self).setVisible(visible)
        if visible:
            # Make sure size is correct
            self.resize(self.parent().size())

    def eventFilter(self, obj, event):
        '''Filter *event* sent to *obj*.

        Maintain sizing of this overlay to match parent widget.

        Disable parent widget of this overlay receiving interaction events
        while this overlay is active.

        '''
        if not isinstance(obj, QtCore.QObject) or not isinstance(
            event, QtCore.QEvent
        ):
            return False

        # Match sizing of parent.
        if obj == self.parent():
            if event.type() == QtCore.QEvent.Type.Resize:
                # Relay event.
                self.resize(event.size())
        return False


class BlockingOverlay(Overlay):
    '''Display a standard blocking overlay over another widget.'''

    @property
    def message(self):
        return self._message

    @message.setter
    def message(self, value):
        self._message = value
        self.messageLabel.setText(value)

    @property
    def icon_data(self):
        return self._icon_data

    @icon_data.setter
    def icon_data(self, value):
        self._icon_data = value

        if not isinstance(self.icon_data, QtGui.QIcon):
            pixmap = QtGui.QPixmap(self.icon_data).scaled(
                self.icon_size,
                self.icon_size,
                QtCore.Qt.AspectRatioMode.KeepAspectRatio,
            )
        else:
            pixmap = self.icon_data.pixmap(
                self.icon_data.actualSize(
                    QtCore.QSize(self.icon_size, self.icon_size)
                )
            )
        self.icon.setPixmap(pixmap)

    def __init__(
        self,
        parent,
        message='Processing',
        icon=':ftrack/titlebar/logo',
        icon_size=120,
    ):
        '''Initialise with *parent*.

        *message* is the message to display on the overlay.

        '''
        super(BlockingOverlay, self).__init__(parent=parent)

        self._message = None
        self._icon_data = None

        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        self.content = QtWidgets.QFrame()
        self.content.setObjectName('content')
        layout.addWidget(
            self.content,
            alignment=QtCore.Qt.AlignmentFlag.AlignCenter
            | QtCore.Qt.AlignmentFlag.AlignTop,
        )

        self.contentLayout = QtWidgets.QVBoxLayout()
        self.contentLayout.setContentsMargins(0, 0, 0, 0)
        self.content.setLayout(self.contentLayout)
        self.icon_size = icon_size
        self.icon = QtWidgets.QLabel()
        self.icon_data = icon
        self.icon.setAlignment(
            QtCore.Qt.AlignmentFlag.AlignCenter
            | QtCore.Qt.AlignmentFlag.AlignTop
        )

        self.contentLayout.addWidget(
            self.icon, alignment=QtCore.Qt.AlignmentFlag.AlignCenter
        )

        self.messageLabel = QtWidgets.QLabel()
        self.messageLabel.setWordWrap(True)
        self.messageLabel.setAlignment(
            QtCore.Qt.AlignmentFlag.AlignCenter
            | QtCore.Qt.AlignmentFlag.AlignBottom
        )

        self.contentLayout.addSpacing(30)

        self.contentLayout.addWidget(self.messageLabel)

        self.message = message

    def setMessage(self, message):
        # TODO: Remove this method when all references to it externally are removed.
        # Keep if for now for backwards compatibility.
        logger.warning(
            'BlockingOverlay.setMessage is deprecated. Use message property instead.'
        )
        self.message = message


class BusyOverlay(BlockingOverlay):
    '''Display a standard busy overlay over another widget.'''

    def __init__(self, parent, message='Processing'):
        '''Initialise with *parent* and busy *message*.'''
        super(BusyOverlay, self).__init__(parent=parent, message=message)

        self.indicator = ftrack_connect.ui.widget.indicator.BusyIndicator()
        self.indicator.setFixedSize(85, 85)

        self.icon.hide()
        self.contentLayout.insertWidget(
            1, self.indicator, alignment=QtCore.Qt.AlignmentFlag.AlignCenter
        )

    def setVisible(self, visible):
        '''Set whether *visible* or not.'''
        if visible:
            self.indicator.start()
        else:
            self.indicator.stop()

        super(BusyOverlay, self).setVisible(visible)


class CancelOverlay(BusyOverlay):
    '''Display a standard busy overlay with cancel button.'''

    def __init__(self, parent, message='Processing'):
        '''Initialise with *parent* and busy *message*.'''
        super(CancelOverlay, self).__init__(parent=parent, message=message)

        self.contentLayout.addSpacing(30)

        loginButton = QtWidgets.QPushButton(text='Cancel')
        loginButton.clicked.connect(self.hide)

        self.contentLayout.addWidget(
            loginButton, alignment=QtCore.Qt.AlignmentFlag.AlignCenter
        )
