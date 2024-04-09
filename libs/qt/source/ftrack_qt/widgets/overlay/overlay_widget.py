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

    @property
    def widget(self):
        '''Return the widget being overlaid.'''
        return self._widget

    def __init__(
        self,
        widget,
        transparent_background=False,
        parent=None,
    ):
        '''
        Initialize Overlay

        :param widget: The widget to put inside the overlay
        :param transparent_background: If True, widget should be made semi transparent together
        with the surrounding area.
        :param parent: The parent dialog or frame
        '''
        super(OverlayWidget, self).__init__(parent=parent)

        self._widget = widget
        self._transparent_background = transparent_background

        self._close_btn = None
        self._fill_color = None
        self._pen_color = None
        self._event_filter_installed = False

        self.pre_build()
        self.build()
        self.post_build()

    def pre_build(self):
        self.setLayout(QtWidgets.QVBoxLayout())
        self.layout().setContentsMargins(10, 10, 10, 10)
        self.layout().setSpacing(2)

    def build(self):
        # Create a container widget to hold the widget to be overlaid.

        h_layout = QtWidgets.QHBoxLayout()
        h_layout.setContentsMargins(0, 0, 0, 0)
        h_layout.addStretch()

        self._close_btn = QtWidgets.QPushButton('')
        self._close_btn.setIcon(MaterialIcon('close', color='#D3D4D6'))
        self._close_btn.setObjectName('borderless')
        self._close_btn.setFixedSize(24, 24)

        h_layout.addWidget(self._close_btn)

        self.layout().addLayout(h_layout)

        self.layout().addWidget(self.widget)
        self.setAutoFillBackground(False)
        if self._transparent_background:
            self.widget.setAutoFillBackground(False)
            self.widget.setStyleSheet('background: transparent;')
        else:
            self.widget.setAutoFillBackground(True)
            self.widget.setStyleSheet('background: #1A2027;')

        self._fill_color = QtGui.QColor(26, 32, 39, 220)
        self._pen_color = QtGui.QColor("#1A2027")

    def post_build(self):
        self._close_btn.clicked.connect(self.close)

    def __del__(self):
        if self._event_filter_installed:
            self._get_main_widget().removeEventFilter(self)

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

    def _get_main_widget(self):
        result = get_framework_main_dialog(self.parent())
        if not result:
            result = get_main_window_from_widget(self.parent())
        return result

    def setVisible(self, visible):
        '''(Override) Set whether *visible* or not.'''
        if visible:
            if not self._event_filter_installed:
                # Install global event filter that will deal with matching parent size
                # and disabling parent interaction when overlay is visible.
                self._get_main_widget().installEventFilter(self)
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
                self._get_main_widget().removeEventFilter(self)
                self._event_filter_installed = False

        super(OverlayWidget, self).setVisible(visible)
        if visible:
            # Make sure size is correct
            self.resize(self._get_main_widget().size())

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
