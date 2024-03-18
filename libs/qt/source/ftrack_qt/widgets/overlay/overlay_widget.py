# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

try:
    from PySide6 import QtWidgets, QtCore, QtGui
except ImportError:
    from PySide2 import QtWidgets, QtCore, QtGui

from ftrack_qt.utils.widget import (
    get_main_window_from_widget,
    get_framework_main_dialog,
)

from ftrack_qt.widgets.icons import MaterialIcon


class OverlayWidget(QtWidgets.QFrame):
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
        transparent_background=False,
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
        super(OverlayWidget, self).__init__(parent=parent)

        self._widget = widget
        self._transparent_background = transparent_background
        self._width_percentage = width_percentage
        self._height_percentage = height_percentage

        self._container_widget = None
        self._close_btn = None
        self._fill_color = None
        self._pen_color = None
        self._event_filter_installed = False

        self.build()
        self.post_build()

    def build(self):
        # Create a container widget to hold the widget to be overlaid.
        self._container_widget = QtWidgets.QFrame(parent=self)
        self._container_widget.setLayout(QtWidgets.QVBoxLayout())

        h_layout = QtWidgets.QHBoxLayout()
        h_layout.setContentsMargins(0, 0, 0, 0)
        h_layout.addStretch()

        self._close_btn = QtWidgets.QPushButton(
            '', parent=self._container_widget
        )
        self._close_btn.setIcon(MaterialIcon('close', color='#D3D4D6'))
        self._close_btn.setObjectName('borderless')
        self._close_btn.setFixedSize(24, 24)

        h_layout.addWidget(self._close_btn)

        self._container_widget.layout().addLayout(h_layout)

        self._container_widget.layout().addWidget(self._widget)
        self._container_widget.setAutoFillBackground(False)
        if self._transparent_background:
            self._container_widget.setAutoFillBackground(False)
            self._container_widget.setStyleSheet('background: transparent;')
        else:
            self._container_widget.setAutoFillBackground(True)
            self._container_widget.setStyleSheet('background: #1A2027;')

        self._fill_color = QtGui.QColor(26, 32, 39, 150)
        self._pen_color = QtGui.QColor("#1A2027")

    def post_build(self):
        self._close_btn.clicked.connect(self.close)

    def __del__(self):
        if self._event_filter_installed:
            application = QtCore.QCoreApplication.instance()
            application.removeEventFilter(self)

    def paintEvent(self, event):
        '''(Override)'''
        super(OverlayWidget, self).paintEvent(event)
        # Paint a transparent overlay over the parent widget.
        size = self.size()  # get current window size
        painter = QtGui.QPainter()
        painter.begin(self)
        painter.setRenderHint(
            QtGui.QPainter.RenderHint.Antialiasing,
            True,
        )
        painter.setPen(self._pen_color)
        painter.setBrush(self._fill_color)
        painter.drawRect(0, 0, size.width(), size.height())
        painter.end()

    def resizeEvent(self, event):
        '''(Override)'''
        super(OverlayWidget, self).resizeEvent(event)
        size = self.size()
        widget_width = size.width() * self._width_percentage
        widget_height = size.height() * self._height_percentage
        widget_x = int((size.width() - widget_width) / 2)
        widget_y = 40  # int(size.height()/2-widget_height/2)
        self._container_widget.resize(widget_width, widget_height)
        self._container_widget.move(widget_x, widget_y)

    def setVisible(self, visible):
        '''(Override) Set whether *visible* or not.'''
        main_window = get_framework_main_dialog(self._container_widget)
        if not main_window:
            main_window = get_main_window_from_widget(self)
        if visible:
            if not self._event_filter_installed:
                # Install global event filter that will deal with matching parent size
                # and disabling parent interaction when overlay is visible.
                main_window.installEventFilter(self)
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
                main_window.removeEventFilter(self)
                self._event_filter_installed = False

        super(OverlayWidget, self).setVisible(visible)
        if visible:
            # Make sure size is correct
            if main_window:
                self.resize(main_window.size())

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
            if event.type() == QtCore.QEvent.Resize:
                # Relay event.
                self.resize(event.size())
        return False

        # Let event propagate.
        return super(OverlayWidget, self).eventFilter(obj, event)
