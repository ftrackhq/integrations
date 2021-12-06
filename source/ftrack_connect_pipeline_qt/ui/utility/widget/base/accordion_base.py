# :coding: utf-8
# :copyright: Copyright (c) 2014-2021 ftrack
from functools import partial

from Qt import QtWidgets, QtCore, QtGui

from ftrack_connect_pipeline_qt import constants
from ftrack_connect_pipeline import constants as pipeline_constants
from ftrack_connect_pipeline_qt.plugin.widgets import BaseOptionsWidget
from ftrack_connect_pipeline_qt.ui.utility.widget.material_icon import MaterialIconWidget


class AccordionBaseWidget(QtWidgets.QWidget):

    def on_collapse(self, collapsed):
        ''' Can be overridden by child. '''
        pass

    def init_header_content(self, layout, collapsed):
        ''' Can be overridden by child. '''
        layout.addStretch()

    @property
    def title(self):
        return self._title

    @property
    def is_collapsed(self):
        return self._is_collapsed

    def __init__(self, parent=None, title=None, checkable=False):
        super(AccordionBaseWidget, self).__init__(parent=parent)

        self._reference_widget = None
        self._is_collapsed = True
        self._header = None
        self._content = None
        self._title = title
        self._widgets = {}
        self._inner_widget_status = {}
        self.checkable = checkable

        self._input_message = 'Initializing...'
        self._input_status = False

        self.pre_build()
        self.build()
        self.post_build()

    @property
    def header(self):
        return self._header

    def set_status(self, status, message):
        # TODO: Instead of run status, implement collector status
        self.header._status.set_status(status, message)

    def pre_build(self):
        self.setLayout(QtWidgets.QVBoxLayout())
        self.layout().setAlignment(QtCore.Qt.AlignTop)
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().setSpacing(1)

    def build(self):
        title_widget = self.init_header(self._title, self._is_collapsed)
        self.layout().addWidget(title_widget)

        content_widget = self._init_content(self._is_collapsed)
        self.layout().addWidget(content_widget)

    def post_build(self):
        self.init_collapsable()
        self.update_input(self._input_message, self._input_status)
        
    def init_header(self, title, collapsed):
        self._header = AccordionHeaderWidget(self,
            title=title, collapsed=collapsed, checkable=self.checkable)
        return self._header

    def _init_content(self, collapsed):
        self._content = QtWidgets.QWidget()
        self._content.setLayout(QtWidgets.QVBoxLayout())
        self._content.setVisible(not collapsed)

        self._content.layout().setContentsMargins(0, 0, 0, 0)
        self._content.layout().setSpacing(0)

        return self._content

    def update_inner_status(self, inner_widget, data):
        status, message = data

        self._inner_widget_status[inner_widget] = status

        all_bool_status = [
            pipeline_constants.status_bool_mapping[_status]
            for _status in list(self._inner_widget_status.values())
        ]
        if all(all_bool_status):
            self.set_status(constants.SUCCESS_STATUS, None)
        else:
            if constants.RUNNING_STATUS in list(self._inner_widget_status.values()):
                self.set_status(constants.RUNNING_STATUS, None)
            else:
                self.set_status(constants.ERROR_STATUS, None)

    def add_option_button(self, title, icon, idx):
        option_button = self._header.add_option_button(title, icon, idx)
        return option_button

    def add_widget(self, widget):
        ''' Add widget to content '''
        self._content.layout().addWidget(widget)
        self._connect_inner_widgets(widget)

    def _connect_inner_widgets(self, widget):
        if issubclass(widget.__class__, BaseOptionsWidget):
            self._widgets[widget] = widget
            widget.status_updated.connect(
                partial(self.update_inner_status, widget)
            )
            return
        inner_widgets = widget.findChildren(BaseOptionsWidget)
        self._widgets[widget] = inner_widgets
        for inner_widget in inner_widgets:
            inner_widget.status_updated.connect(
                partial(self.update_inner_status, inner_widget)
            )

    def count_widgets(self):
        return self._content.layout().count()

    def get_witget_at(self, index):
        return self._content.layout().itemAt(index).widget()

    def init_collapsable(self):
        self._header.clicked.connect(self.toggle_collapsed)
        self._header.checked.connect(self.enable_content)

    def is_checked(self):
        if self._header.checkable:
            return self._header.checkbox.isChecked()
        return True

    def set_checked(self, checked):
        if self._header.checkable:
            return self._header.checkbox.setChecked(checked)

    def toggle_collapsed(self):
        self._content.setVisible(self._is_collapsed)
        self._is_collapsed = not self._is_collapsed
        self._header.update_arrow_icon(int(self._is_collapsed))
        self.on_collapse(self.is_collapsed)

    def enable_content(self, check_enabled):
        self._content.setEnabled(check_enabled)

    def paint_title(self, color):
        self._header._title_label.setStyleSheet(
            "color: {}".format(color)
        )

    def set_unavailable(self):
        self.setToolTip('This component is not available in ftrack')
        if not self.checkable:
            self.paint_title("red")
            self.setToolTip(
                'This component is mandatory and is not available in ftrack'
            )
        self.set_checked(False)
        self.setEnabled(False)

    def set_default_state(self):
        self.setToolTip("")
        if not self.checkable:
            self._header._title_label.setStyleSheet("")
        self.set_checked(True)
        self.setEnabled(True)

    def update_input(self, message, status):
        '''Update the accordion input summary, should be overridden by child.'''
        raise NotImplementedError()


class AccordionHeaderWidget(QtWidgets.QFrame):
    ''' Container for accordion header - holding checkbox, title, user content
    and expander button.'''
    clicked = QtCore.Signal()
    checked = QtCore.Signal(object)

    @property
    def checkbox(self):
        return self._checkbox

    @property
    def content(self):
        ''' Return the content widget where user widgets can be added.'''
        return self._content

    def __init__(self, accordion, parent=None, title=None, collapsed=False,
                 checkable=False):
        super(AccordionHeaderWidget, self).__init__(parent=parent)

        self._accordion = accordion

        self._checkbox = None
        self._title_label = None
        self._status = None
        self._content = None
        self._arrow = None

        self.title = title
        self.initial_collapse = collapsed
        self.checkable = checkable

        self.pre_build()
        self.build()
        self.post_build()

    def pre_build(self):
        self.setMinimumHeight(24)
        self.move(QtCore.QPoint(24, 0))
        self.setLayout(QtWidgets.QHBoxLayout())
        self.layout().setContentsMargins(15, 0, 0, 0)

    def build(self):
        self.layout().addWidget(self.init_checkbox(True, self.checkable))
        self.layout().addWidget(self.init_title(self.title))
        self.layout().addWidget(self.init_content())
        self.layout().addWidget(self.init_arrow(self.initial_collapse))

    def post_build(self):
        if self.checkbox:
            self._checkbox.stateChanged.connect(self.enable_content)

    def init_checkbox(self, checked, enabled):
        self._checkbox = QtWidgets.QCheckBox()
        self._checkbox.setChecked(checked)
        self._checkbox.setEnabled(enabled)
        return self._checkbox

    def init_title(self, title=None):
        self._title_label = QtWidgets.QLabel(title or '')
        self._title_label.setStyleSheet("border:0px")
        if not title:
            self._title_label.hide()
        return self._title_label

    def init_content(self):
        self._content = QtWidgets.QWidget()
        self._content.setLayout(QtWidgets.QHBoxLayout())
        self._content.layout().setContentsMargins(0, 0, 0, 0)
        self._content.layout().setSpacing(1)
        self._accordion.init_header_content(self._content.layout(),
                                            self._accordion.is_collapsed)
        return self._content

    # def init_status(self):
    #     self._status = AccordionStatus()
    #     return self._status

    def update_arrow_icon(self, collapsed):
        if collapsed:
            icon_name = 'chevron-down'
        else:
            icon_name ='chevron-up'
        self._arrow.set_icon(name=icon_name)

    def init_arrow(self, collapsed):
        self._arrow = MaterialIconWidget()
        self.update_arrow_icon(collapsed)
        return self._arrow

    def mousePressEvent(self, event):
        self.clicked.emit()
        return super(AccordionHeaderWidget, self).mousePressEvent(event)

    def enable_content(self, check_enabled):
        self._title_label.setEnabled(check_enabled)
        self.checked.emit(check_enabled)
