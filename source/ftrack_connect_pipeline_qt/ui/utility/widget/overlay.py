# :coding: utf-8
# :copyright: Copyright (c) 2014-2021 ftrack

from Qt import QtGui, QtCore, QtWidgets

from ftrack_connect_pipeline_qt import utils

from ftrack_connect_pipeline_qt.ui.utility.widget import icon


class Overlay(QtWidgets.QFrame):
    '''
    Display a semi-transparent overlay over another widget.

    While the overlay is active, the main parent window and its children will not
    receive interaction events from the user (e.g. focus).
    '''

    def __init__(
        self,
        widget,
        width_percentage=0.95,
        height_percentage=0.6,
        transparent_background=True,
        parent=None,
    ):
        '''
        Initialize Overlay

        :param widget: The widget to put inside the overlay
        :param width_percentage: The percentage (0-100) of width it should consume
        :param height_percentage: The percentage (0-100) of height it should consume
        :param transparent_background: If True(default), overlay background should be made semi transparent
        :param parent: The parent dialog or frame
        '''
        super(Overlay, self).__init__(parent=parent)

        self._transparent_background = transparent_background
        self._width_percentage = width_percentage
        self._height_percentage = height_percentage
        self._event_filter_installed = False

        self.widget = QtWidgets.QFrame(parent=self)
        self.widget.setProperty('background', 'ftrack')
        self.widget.setLayout(QtWidgets.QVBoxLayout())
        self.widget.layout().setContentsMargins(1, 20, 1, 1)
        self.widget.layout().addWidget(widget)
        if self._transparent_background:
            widget.setAutoFillBackground(False)
            widget.setStyleSheet('background: transparent;')
        else:
            widget.setProperty('background', 'ftrack')

        self.close_btn = QtWidgets.QPushButton('', parent=self)
        self.close_btn.setIcon(icon.MaterialIcon('close', color='#D3d4D6'))
        self.close_btn.setObjectName('borderless')
        self.close_btn.setFixedSize(24, 24)
        self.close_btn.clicked.connect(self.close)

        self.fill_color = QtGui.QColor(26, 32, 39, 200)
        self.pen_color = QtGui.QColor("#1A2027")

    def __del__(self):
        if self._event_filter_installed:
            application = QtCore.QCoreApplication.instance()
            application.removeEventFilter(self)

    def paintEvent(self, event):
        '''(Override)'''
        super(Overlay, self).paintEvent(event)
        # get current window size
        size = self.size()
        painter = QtGui.QPainter()
        painter.begin(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing, True)
        painter.setPen(self.pen_color)
        painter.setBrush(self.fill_color)
        painter.drawRect(0, 0, size.width(), size.height())
        painter.end()

    def resizeEvent(self, event):
        '''(Override)'''
        super(Overlay, self).resizeEvent(event)
        size = self.size()
        widget_width = size.width() * self._width_percentage
        widget_height = size.height() * self._height_percentage
        widget_x = int((size.width() - widget_width) / 2)
        widget_y = 40  # int(size.height()/2-widget_height/2)
        self.widget.resize(widget_width, widget_height)
        self.widget.move(widget_x, widget_y)
        # Move the close button to the desired position
        self.close_btn.move(widget_x + widget_width - 22, widget_y)

    def setVisible(self, visible):
        '''(Override) Set whether *visible* or not.'''
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
            main_window = utils.get_main_framework_window_from_widget(
                self.widget
            )
            if main_window:
                self.resize(main_window.size())

    def eventFilter(self, obj, event):
        '''Filter *event* sent to *obj*.

        Maintain sizing of this overlay to match parent widget.

        Disable parent widget of this overlay receiving interaction events
        while this overlay is active.

        '''
        if not isinstance(event, QtCore.QEvent):
            return False

        # Match sizing of parent.
        if obj == self.parent():
            if event.type() == QtCore.QEvent.Resize:
                # Relay event.
                self.resize(event.size())

        # TODO: Evaluate if this commented code is still valid. It's currently
        #  deactivated because was disabling the editable of the inner widgets.
        #
        #     # Prevent interaction events reaching parent and its child widgets
        #     # while this overlay is visible. To do this, intercept appropriate
        #     # events (currently focus events) and handle them by skipping child
        #     # widgets of the target parent. This prevents the user from tabbing
        #     # into a widget that is currently overlaid.
        #     #
        #     # Note: Previous solutions attempted to use a simpler method of setting
        #     # the overlaid widget to disabled. This doesn't work because the overlay
        #     # itself is a child of the overlaid widget and Qt does not allow a child
        #     # of a disabled widget to be enabled. Attempting to manage manually the
        #     # enabled state of each child grows too complex as have to remember the
        #     # initial state of each widget when the overlay is shown and then revert
        #     # to it on hide.
        #     if event.type() == QtCore.QEvent.FocusIn and obj != self:
        #         parent = self.parent()
        #         if isinstance(obj, QtWidgets.QWidget) and parent.isAncestorOf(obj):
        #             # Ensure the targeted object loses its focus.
        #             obj.clearFocus()
        #
        #             # Loop through available widgets to move focus to. If an
        #             # available widget is not a child of the parent widget targeted
        #             # by this overlay then move focus to it, respecting requested
        #             # focus direction.
        #             seen = []
        #             candidate = obj
        #             reason = event.reason()
        #
        #             while True:
        #                 if reason == QtCore.Qt.TabFocusReason:
        #                     candidate = candidate.nextInFocusChain()
        #                 elif reason == QtCore.Qt.BacktabFocusReason:
        #                     candidate = candidate.previousInFocusChain()
        #                 else:
        #                     break
        #
        #                 if candidate in seen:
        #                     # No other widget available for focus.
        #                     break
        #
        #                 # Keep track of candidates to avoid infinite recursion.
        #                 seen.append(candidate)
        #
        #                 if isinstance(
        #                     candidate, QtWidgets.QWidget
        #                 ) and not parent.isAncestorOf(candidate):
        #                     candidate.setFocus(event.reason())
        #                     break
        #
        #             # Swallow event.
        #             return True
        #
        # Let event propagate.
        return super(Overlay, self).eventFilter(obj, event)
