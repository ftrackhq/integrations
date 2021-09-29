# :coding: utf-8
# :copyright: Copyright (c) 2014-2021 ftrack

from Qt import QtGui, QtCore, QtWidgets

class Overlay(QtWidgets.QWidget):
    '''Display a transparent overlay over another widget.

    Customise the background colour using stylesheets. The widget has an object
    name of "overlay".

    While the overlay is active, the target widget and its children will not
    receive interaction events from the user (e.g. focus).

    '''

    def __init__(self, widget, parent=None):
        '''Initialise overlay for target *parent*.'''
        super(Overlay, self).__init__(parent=parent)
        self.setObjectName('overlay')

        self.widget = widget
        self.widget.setParent(self)
        self.widget.setAutoFillBackground(True)

        self.close_btn = QtWidgets.QPushButton("X", self)
        self.close_btn.setStyleSheet(
            "background-color: rgba(0, 0, 0, 0);"
        )
        self.close_btn.setFixedSize(30, 30)
        self.close_btn.clicked.connect(self.close)

        self.fill_color = QtGui.QColor(30, 30, 30, 120)
        self.pen_color = QtGui.QColor("#333333")

        # Install global event filter that will deal with matching parent size
        # and disabling parent interaction when overlay is visible.
        application = QtCore.QCoreApplication.instance()
        application.installEventFilter(self)


    def paintEvent(self, event):
        super(Overlay, self).paintEvent(event)
        # get current window size
        s = self.size()
        qp = QtGui.QPainter()
        qp.begin(self)
        qp.setRenderHint(QtGui.QPainter.Antialiasing, True)
        qp.setPen(self.pen_color)
        qp.setBrush(self.fill_color)
        qp.drawRect(0, 0, s.width(), s.height())
        qp.end()

    def resizeEvent(self, event):
        super(Overlay, self).resizeEvent(event)
        s = self.size()
        popup_width = s.width() - (s.width() * 0.2)
        popup_height = s.height() - (s.height() * 0.2)
        ow = int(s.width()/2-popup_width/2)
        oh = int(s.height()/2-popup_height/2)
        self.widget.resize(popup_width, popup_height)
        self.widget.move(ow, oh)
        # Move the close button to the desired position
        self.close_btn.move(ow, oh)

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
        self.resize(self.widget.window().size())

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
                        isinstance(candidate, QtWidgets.QWidget)
                        and not parent.isAncestorOf(candidate)
                    ):
                        candidate.setFocus(event.reason())
                        break

                # Swallow event.
                return True

        # Let event propagate.
        return False
