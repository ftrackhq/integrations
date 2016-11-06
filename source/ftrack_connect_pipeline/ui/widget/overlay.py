# :coding: utf-8
# :copyright: Copyright (c) 2016 ftrack

from QtExt import QtGui, QtCore, QtWidgets

import ftrack_connect_pipeline.ui.widget.indicator


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
            QtWidgets.QFrame.StyledPanel | QtWidgets.QFrame.Plain
        )

        # Install global event filter that will deal with matching parent size
        # and disabling parent interaction when overlay is visible.
        application = QtCore.QCoreApplication.instance()
        application.installEventFilter(self)

    def setVisible(self, visible):
        '''Set whether *visible* or not.'''
        if visible:
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

        super(Overlay, self).setVisible(visible)

    def eventFilter(self, obj, event):
        '''Filter *event* sent to *obj*.

        Maintain sizing of this overlay to match parent widget.

        Disable parent widget of this overlay receiving interaction events
        while this overlay is active.

        '''
        # Match sizing of parent.
        if obj == self.parent():
            if event.type() == QtCore.QEvent.Resize:
                # Relay event.
                self.resize(event.size())

        # Prevent interaction events reaching parent and its child widgets
        # while this overlay is visible. To do this, intercept appropriate
        # events (currently focus events) and handle them by skipping child
        # widgets of the target parent. This prevents the user from tabbing
        # into a widget that is currently overlaid.
        #
        # Note: Previous solutions attempted to use a simpler method of setting
        # the overlaid widget to disabled. This doesn't work because the overlay
        # itself is a child of the overlaid widget and Qt does not allow a child
        # of a disabled widget to be enabled. Attempting to manage manually the
        # enabled state of each child grows too complex as have to remember the
        # initial state of each widget when the overlay is shown and then revert
        # to it on hide.
        if (
            self.isVisible()
            and obj != self
            and event.type() == QtCore.QEvent.FocusIn
        ):
            parent = self.parent()
            if (
                isinstance(obj, QtWidgets.QWidget)
                and parent.isAncestorOf(obj)
            ):
                # Ensure the targeted object loses its focus.
                obj.clearFocus()

                # Loop through available widgets to move focus to. If an
                # available widget is not a child of the parent widget targeted
                # by this overlay then move focus to it, respecting requested
                # focus direction.
                seen = []
                candidate = obj
                reason = event.reason()

                while True:
                    if reason == QtCore.Qt.TabFocusReason:
                        candidate = candidate.nextInFocusChain()
                    elif reason == QtCore.Qt.BacktabFocusReason:
                        candidate = candidate.previousInFocusChain()
                    else:
                        break

                    if candidate in seen:
                        # No other widget available for focus.
                        break

                    # Keep track of candidates to avoid infinite recursion.
                    seen.append(candidate)

                    if (
                        isinstance(candidate, QtGui.QWidget)
                        and not parent.isAncestorOf(candidate)
                    ):
                        candidate.setFocus(event.reason())
                        break

                # Swallow event.
                return True

        # Let event propagate.
        return False


class BlockingOverlay(Overlay):
    '''Display a standard blocking overlay over another widget.'''

    def __init__(
        self, parent, message='Processing',
        icon=':ftrack/image/default/ftrackLogoColor'
    ):
        '''Initialise with *parent*.

         *message* is the message to display on the overlay.

         '''
        super(BlockingOverlay, self).__init__(parent)
        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        self.content = QtWidgets.QFrame()
        self.content.setObjectName('content')
        layout.addWidget(
            self.content, alignment=QtCore.Qt.AlignCenter
        )

        self.contentLayout = QtWidgets.QVBoxLayout()
        self.contentLayout.setContentsMargins(0, 0, 0, 0)
        self.content.setLayout(self.contentLayout)

        self.icon = QtWidgets.QLabel()
        pixmap = QtGui.QPixmap(icon)
        self.icon.setPixmap(
            pixmap.scaledToHeight(36, mode=QtCore.Qt.SmoothTransformation)
        )
        self.icon.setAlignment(QtCore.Qt.AlignCenter)
        self.contentLayout.addWidget(self.icon)

        self.messageLabel = QtWidgets.QLabel()
        self.messageLabel.setWordWrap(True)
        self.messageLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.contentLayout.addWidget(self.messageLabel)

        self.setStyleSheet('''
            BlockingOverlay {
                background-color: rgba(250, 250, 250, 200);
                border: none;
            }

            BlockingOverlay QFrame#content {
                padding: 0px;
                border: 80px solid transparent;
                background-color: transparent;
                border-image: url(:ftrack/image/default/boxShadow) 140 stretch;
            }

            BlockingOverlay QLabel {
                background: transparent;
            }
        ''')

        self.setMessage(message)

    def message(self):
        '''Return current message.'''
        return self._message

    def setMessage(self, message):
        '''Set current message to display.'''
        self._message = message
        self.messageLabel.setText(message)


class BusyOverlay(BlockingOverlay):
    '''Display a standard busy overlay over another widget.'''

    def __init__(self, parent, message='Processing'):
        '''Initialise with *parent* and busy *message*.'''
        super(BusyOverlay, self).__init__(parent, message=message)

        self.indicator = ftrack_connect_pipeline.ui.widget.indicator.BusyIndicator()
        self.indicator.setFixedSize(85, 85)

        self.icon.hide()
        self.contentLayout.insertWidget(
            1, self.indicator, alignment=QtCore.Qt.AlignCenter
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
        super(CancelOverlay, self).__init__(parent, message=message)

        self.contentLayout.addSpacing(10)

        loginButton = QtWidgets.QPushButton(text='Cancel')
        loginButton.clicked.connect(self.hide)

        self.contentLayout.addWidget(
            loginButton, alignment=QtCore.Qt.AlignCenter
        )
