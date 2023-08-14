# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from Qt import QtWidgets, QtCore, QtGui

from ftrack_qt.utils.widget import set_property
from ftrack_qt.widgets.headers import AccordionHeaderWidget

# TODO: Review this code, make it cleaner and easier to modif. If accordion
#  widget is meant to work in different ways, create a variation of it
#  (Inheriting from this one) in another file.
class AccordionBaseWidget(QtWidgets.QFrame):
    '''A utility accordion widget providing a header which can be expanded to show content'''

    clicked = QtCore.Signal(object)  # Emitted when accordion is clicked
    doubleClicked = QtCore.Signal(
        object
    )  # Emitted when accordion is double clicked
    checkedStateChanged = QtCore.Signal(
        object
    )  # Emitted when checked state changed

    CHECK_MODE_NONE = -1  # Not checkable and not showing checkbox
    CHECK_MODE_CHECKBOX = 0  # Checkable and visible
    CHECK_MODE_CHECKBOX_DISABLED = 1  # Visible but not checkable

    def on_collapse(self, collapsed):
        '''(Optional) To be overridden by child'''
        pass

    def init_content(self, content_layout):
        '''(Optional) To be overridden by child'''
        pass

    @property
    def title(self):
        '''Return the title text shown in header by default'''
        return self._title

    @property
    def selectable(self):
        '''Return the current selection mode'''
        return self._selectable

    @property
    def check_mode(self):
        '''Return the current check (box) mode'''
        return self._check_mode

    @property
    def checkable(self):
        '''Return True if accordion is checkable with a checkbox'''
        return self._checkable

    @property
    def show_checkbox(self):
        '''Return True if accordion is checkable with a checkbox'''
        return self._show_checkbox

    @checkable.setter
    def checkable(self, value):
        '''Set the checkable property'''
        self._check_mode = (
            self.CHECK_MODE_CHECKBOX
            if value
            else self.CHECK_MODE_CHECKBOX_DISABLED
        )
        if self._header_widget and self._header_widget.checkbox:
            self._header_widget.checkbox.setEnabled(
                self._check_mode == self.CHECK_MODE_CHECKBOX
            )

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
        self._selected = value

    @property
    def checked(self):
        '''(Checkable) Return True if checked'''
        return self._checked

    @checked.setter
    def checked(self, value):
        '''Set the checked property'''
        if self.isEnabled():
            prev_checked = self._checked
            self._checked = value
            if self._header_widget:
                if self.check_mode == self.CHECK_MODE_CHECKBOX:
                    self._header_widget.checkbox.setChecked(value)
                self._header_widget.title_label.setEnabled(self._checked)
            self.enable_content()
            if self._checked != prev_checked:
                self.checkedStateChanged.emit(self)

    @property
    def header_widget(self):
        '''Return header widget'''
        return self._header_widget

    @property
    def content_widget(self):
        '''Return content widget'''
        return self._content_widget

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
        docked=False,
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

        self._selectable = selectable
        self._checkable = checkable
        self._show_checkbox = show_checkbox
        self._header_widget = None
        self._content_widget = None
        self._title = title
        self._inner_widget_status = {}
        self._selected = selected
        self._checked = checked
        self._collapsed = collapsed
        self._checked = checked
        self._collapsable = collapsable
        self._docked = docked

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

        # Create the main_wdget
        main_widget = QtWidgets.QWidget()
        main_widget.setLayout(QtWidgets.QVBoxLayout())
        main_widget.layout().setAlignment(QtCore.Qt.AlignTop)
        main_widget.layout().setContentsMargins(0, 0, 0, 0)
        main_widget.layout().setSpacing(1)

        # Create Header
        self._header_widget = QtWidgets.QFrame()
        self._header_widget = AccordionHeaderWidget(title=self.title)

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
        if self.checkable:
            self._header_widget.checkbox.stateChanged.connect(
                self._on_header_checkbox_checked
            )
        self._header_widget.clicked.connect(self._on_header_clicked)
        self._header_widget.arrow_clicked.connect(self._on_header_arrow_clicked)
        self._content_widget.setVisible(not self._collapsed)
        if self.checkable:
            self.enable_content()

    def add_widget(self, widget):
        '''Add widget to content'''
        self._content_widget.layout().addWidget(widget)

    def count_widgets(self):
        '''Return the number of widgets within the content'''
        return self._content_widget.layout().count()

    def get_widget_at(self, index):
        '''Return the content widget at *index*'''
        return self._content_widget.layout().itemAt(index).widget()

    def set_selected(self, selected):
        '''Set selected property to *selected*, returns True is selection changed'''
        retval = False
        if self.isEnabled():
            if self._selected != selected:
                retval = True
            self._selected = selected
            self.update_accordion()
        return retval

    def enable_content(self):
        '''Enable content widget depending on if accordion is checked or not'''
        if self._content_widget:
            self._content_widget.setEnabled(self.checked)

    def paint_title(self, color):
        '''Put a foreground *color* on header title label'''
        self._header_widget._title_label.setStyleSheet("color: {}".format(color))

    def set_indicator_color(self, color):
        '''Set the left indicator visibility depending on *color*'''
        set_property(
            self._indicator_widget,
            'indicator',
            color or 'green',
        )
        if not self._indicator_widget.isVisible():
            self._indicator_widget.setVisible(True)

    def _on_header_checkbox_checked(self):
        '''Callback on enable checkbox user interaction'''
        self.checked = self._header_widget.checkbox.isChecked()

    def _on_header_clicked(self, event):
        '''Callback on header user click'''
        if not self.selectable:
            if event.button() != QtCore.Qt.RightButton:
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
        self.on_collapse(self.collapsed)
        self._content_widget.setVisible(not self._collapsed)

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

