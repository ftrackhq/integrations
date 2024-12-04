# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

try:
    from PySide6 import QtWidgets, QtCore
except ImportError:
    from PySide2 import QtWidgets, QtCore

from ftrack_qt.utils.widget import set_property
from ftrack_qt.widgets.headers import AccordionHeaderWidget


class AccordionBaseWidget(QtWidgets.QFrame):
    '''A utility accordion widget providing a header which can be expanded to show content'''

    clicked = QtCore.Signal(object)  # Emitted when accordion is clicked
    doubleClicked = QtCore.Signal(
        object
    )  # Emitted when accordion is double clicked
    show_options_overlay = QtCore.Signal(object)
    hide_options_overlay = QtCore.Signal()
    enabled_changed = QtCore.Signal(object)

    @property
    def title(self):
        '''Return the title text shown in header by default'''
        return self._title

    @property
    def selectable(self):
        '''Return the current selection mode'''
        return self._selectable

    @property
    def checkable(self):
        '''Return True if accordion is checkable with a checkbox'''
        return self._checkable

    @property
    def show_checkbox(self):
        '''Return True if accordion is checkable with a checkbox'''
        return self._show_checkbox

    @property
    def collapsed(self):
        '''Return True if accordion is collapsed - content hidden (default)'''
        return self._collapsed

    @property
    def collapsable(self):
        '''Return True if accordion is collapsable - content can be hidden (default)'''
        return self._collapsable

    @property
    def selected(self):
        '''Return True if accordion is selected'''
        return self._selected

    @selected.setter
    def selected(self, value):
        '''Set accordion selected property'''
        if self.isEnabled() and self.selectable:
            self._selected = value
            self.update_accordion()

    @property
    def checked(self):
        '''(Checkable) Return True if checked'''
        return self._checked

    def __init__(
        self,
        selectable=False,
        show_checkbox=False,
        checkable=False,
        title=None,
        selected=False,
        checked=True,
        collapsable=True,
        collapsed=True,
        parent=None,
    ):
        '''
        Initialize base accordion widget

        :param select_mode: Mode telling if accordion should be selectable or not
        :param check_mode: Mode telling if accordion should be checkale or not
        :param title: The default title text to show in accordion header
        :param selected: Flag telling if accordion should be initially selected or not
        :param checked: Flag telling if accordion should be initially checked or not
        :param collapsable: Flag telling if accordion is collapsable or not
        :param collapsed: Flag telling if accordion should be initially collapsed or not
        :param docked: Flag telling if accordion is docked in DCC or within an ftrack dialog - drives the style
        :param parent:  the parent dialog or frame
        '''
        super(AccordionBaseWidget, self).__init__(parent=parent)

        self._indicator_widget = None
        self._header_widget = None
        self._content_widget = None

        self._selectable = selectable
        self._checkable = checkable
        self._show_checkbox = show_checkbox
        self._title = title
        self._collapsable = collapsable

        self._selected = selected
        self._checked = checked
        self._collapsed = collapsed

        self.pre_build()
        self.build()
        self.post_build()

    def set_status(self, status, message):
        self._header_widget.set_status(status, message)

    def pre_build(self):
        self.setLayout(QtWidgets.QHBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().setSpacing(0)

    def build(self):
        # Create the indicator widget
        self._indicator_widget = QtWidgets.QFrame()
        self._indicator_widget.setMaximumWidth(4)
        self._indicator_widget.setMinimumWidth(4)
        self._indicator_widget.setVisible(False)

        self.layout().addWidget(self._indicator_widget)

        # Create the main_widget
        main_widget = QtWidgets.QWidget()
        main_widget.setLayout(QtWidgets.QVBoxLayout())
        main_widget.layout().setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)
        main_widget.layout().setContentsMargins(0, 0, 0, 0)
        main_widget.layout().setSpacing(1)

        # Create Header
        self._header_widget = AccordionHeaderWidget(
            title=self.title,
            checkable=self.checkable,
            checked=self.checked,
            show_checkbox=self.show_checkbox,
            collapsable=self.collapsable,
            collapsed=self.collapsed,
        )

        # Add header to main widget
        main_widget.layout().addWidget(self._header_widget)

        # Create content widget
        self._content_widget = QtWidgets.QFrame()
        self._content_widget.setLayout(QtWidgets.QVBoxLayout())
        self._content_widget.layout().setContentsMargins(2, 2, 2, 2)
        self._content_widget.layout().setSpacing(0)

        # Add content widget to main widget
        main_widget.layout().addWidget(self._content_widget)

        # Add main_widget to main layout
        self.layout().addWidget(main_widget)

    def post_build(self):
        self._header_widget.checkbox_status_changed.connect(
            self._on_checkbox_status_changed
        )
        self._header_widget.clicked.connect(self._on_header_clicked)
        self._header_widget.arrow_clicked.connect(
            self._on_header_arrow_clicked
        )
        self._header_widget.show_options_overlay.connect(
            self._on_show_options_overlay_callback
        )
        self._header_widget.hide_options_overlay.connect(
            self._on_hide_options_overlay_callback
        )
        self._content_widget.setVisible(not self._collapsed)
        self._content_widget.setEnabled(self.checked)

    def _on_show_options_overlay_callback(self, widget):
        self.show_options_overlay.emit(widget)

    def _on_hide_options_overlay_callback(self):
        self.hide_options_overlay.emit()

    def add_option_widget(self, widget, section_name):
        self._header_widget.add_option_widget(widget, section_name)

    def add_widget(self, widget):
        '''Add widget to content'''
        self._content_widget.layout().addWidget(widget)

    def count_widgets(self):
        '''Return the number of widgets within the content'''
        return self._content_widget.layout().count()

    def get_widget_at(self, index):
        '''Return the content widget at *index*'''
        return self._content_widget.layout().itemAt(index).widget()

    def paint_title(self, color):
        '''Put a foreground *color* on header title label'''
        self._header_widget._title_label.setStyleSheet(
            "color: {}".format(color)
        )

    def set_indicator_color(self, color):
        '''Set the left indicator visibility depending on *color*'''
        set_property(
            self._indicator_widget,
            'indicator',
            color or 'green',
        )
        if not self._indicator_widget.isVisible():
            self._indicator_widget.setVisible(True)

    def _on_checkbox_status_changed(self, checked):
        '''Callback on enable checkbox user interaction'''
        self._checked = checked
        self._content_widget.setEnabled(self.checked)
        self.enabled_changed.emit(self.checked)

    def _on_header_clicked(self, event):
        '''Callback on header user click'''
        if not self.selectable:
            if event.button() != (QtCore.Qt.MouseButton.RightButton):
                self.toggle_collapsed()

    def _on_header_arrow_clicked(self, event):
        '''Callback on header arrow user click'''
        if self.selectable:
            # This is the way to collapse
            self.toggle_collapsed()

    def toggle_collapsed(self):
        '''Toggle the accordion collapsed state'''
        self._collapsed = not self._collapsed
        self._header_widget.update_arrow_icon(int(self.collapsed))
        self._on_collapse(self.collapsed)
        self._content_widget.setVisible(not self._collapsed)

    def _on_collapse(self, collapsed):
        '''(Optional) To be overridden by child'''
        pass

    def mousePressEvent(self, event):
        '''(Override)'''
        self.clicked.emit(event)
        self.on_click(event)
        return super(AccordionBaseWidget, self).mousePressEvent(event)

    def on_click(self, event):
        '''Callback on accordion user click, to be overridden by child'''
        pass

    def mouseDoubleClickEvent(self, event):
        '''(Override)'''
        self.doubleClicked.emit(event)
        self.on_double_click(event)
        return super(AccordionBaseWidget, self).mouseDoubleClickEvent(event)

    def on_double_click(self, event):
        '''Callback on accordion user double click, to be overridden by child'''
        self.toggle_collapsed()

    def update_accordion(self):
        '''Update accordion background depending on selection state'''
        if self.selectable:
            set_property(
                self,
                'background',
                'selected' if self._selected else 'transparent',
            )

    def teardown(self):
        '''Teardown the header widget - properly cleanup the options overlay'''
        self._header_widget.teardown()
        self._header_widget.deleteLater()
