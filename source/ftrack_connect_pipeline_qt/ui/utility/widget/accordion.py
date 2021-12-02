from functools import partial
import qtawesome as qta

from Qt import QtWidgets, QtCore, QtGui

from ftrack_connect_pipeline_qt import constants
from ftrack_connect_pipeline import constants as pipeline_constants
from ftrack_connect_pipeline_qt.plugin.widgets import BaseOptionsWidget
from ftrack_connect_pipeline_qt.ui.utility.widget import overlay
from ftrack_connect_pipeline_qt import utils
from ftrack_connect_pipeline_qt.ui.utility.widget import line


class AccordionWidget(QtWidgets.QWidget):
    @property
    def title(self):
        return self._title

    def __init__(self, parent=None, title=None, checkable=False):
        super(AccordionWidget, self).__init__(parent=parent)

        self._reference_widget = None
        self._is_collapsed = True
        self._title_frame = None
        self._content, self._content_layout = (None, None)
        self._title = title
        self._widgets = {}
        self._inner_widget_status = {}
        self.checkable = checkable

        self.pre_build()
        self.build()
        self.post_build()

    def set_status(self, status, message):
        # TODO: Instead of run status, implement collector status
        self._title_frame._status.set_status(status, message)

    def pre_build(self):
        self._main_v_layout = QtWidgets.QVBoxLayout()
        self._main_v_layout.setAlignment(QtCore.Qt.AlignTop)
        self._main_v_layout.setContentsMargins(0, 0, 0, 0)
        self._main_v_layout.setSpacing(1)
        self.setLayout(self._main_v_layout)

    def build(self):
        title_widget = self.init_title_frame(self._title, self._is_collapsed)
        self._main_v_layout.addWidget(title_widget)

        content_widget = self.init_content(self._is_collapsed)

        self._main_v_layout.addWidget(content_widget)

    def post_build(self):
        self.init_collapsable()

    def init_title_frame(self, title, collapsed):
        self._title_frame = AccordionTitleWidget(
            title=title, collapsed=collapsed, checkable=self.checkable)
        return self._title_frame

    def init_content(self, collapsed):
        self._content = QtWidgets.QWidget()
        self._content_layout = QtWidgets.QVBoxLayout()

        self._content.setLayout(self._content_layout)
        self._content.setVisible(not collapsed)

        self._content_layout.setContentsMargins(0, 0, 0, 0)
        self._content_layout.setSpacing(0)

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
        option_button = self._title_frame.add_option_button(title, icon, idx)
        return option_button

    def get_extra_button_by_title(self, title):
        return self._title_frame.extra_buttons.get(title)

    def add_widget(self, widget):
        self._content_layout.addWidget(widget)
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
        return self._content_layout.count()

    def get_witget_at(self, index):
        return self._content_layout.itemAt(index).widget()

    def init_collapsable(self):
        self._title_frame.clicked.connect(self.toggle_collapsed)
        self._title_frame.checked.connect(self.enable_content)

    def is_checked(self):
        if self._title_frame.checkable:
            return self._title_frame.checkbox.isChecked()
        return True

    def set_checked(self, checked):
        if self._title_frame.checkable:
            return self._title_frame.checkbox.setChecked(checked)

    def toggle_collapsed(self):
        self._content.setVisible(self._is_collapsed)
        self._is_collapsed = not self._is_collapsed
        self._title_frame._arrow.set_arrow(int(self._is_collapsed))

    def enable_content(self, check_enabled):
        self._content.setEnabled(check_enabled)

    def paint_title(self, color):
        self._title_frame._title_label.setStyleSheet(
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
            self._title_frame._title_label.setStyleSheet("")
        self.set_checked(True)
        self.setEnabled(True)


class AccordionTitleWidget(QtWidgets.QFrame):
    clicked = QtCore.Signal()
    checked = QtCore.Signal(object)

    @property
    def checkbox(self):
        return self._checkbox

    @property
    def extra_buttons(self):
        return self._extra_buttons

    def __init__(self, parent=None, title="", collapsed=False, checkable=False):
        super(AccordionTitleWidget, self).__init__(parent=parent)

        self._arrow = None
        self._title_label = None
        self._status = None
        self._checkbox = None
        self._extra_buttons ={}

        self.title = title
        self.initial_collapse = collapsed
        self.checkable = checkable


        self.pre_build()
        self.build()
        self.post_build()

    def pre_build(self):
        self.setMinimumHeight(24)
        self.move(QtCore.QPoint(24, 0))
        self._hlayout = QtWidgets.QHBoxLayout(self)
        self._hlayout.setContentsMargins(15, 0, 0, 0)

    def build(self):
        self._hlayout.addWidget(self.init_checkbox(True, self.checkable))
        self._hlayout.addWidget(self.init_title(self.title))
        self._hlayout.addStretch()
        self._hlayout.addWidget(line.Line(horizontal=True))
        self._hlayout.addWidget(self.init_status())
        self._hlayout.addWidget(line.Line(horizontal=True))
        self._hlayout.addWidget(self.init_arrow(self.initial_collapse))

    def post_build(self):
        if self.checkbox:
            self._checkbox.stateChanged.connect(self.enable_content)

    def add_option_button(self, title, icon, idx):
        extra_button = self.init_options_button(title, icon)
        self._hlayout.insertWidget(idx, extra_button)
        return extra_button

    def init_options_button(self, title, icon):
        extra_button = OptionsButton(title, icon)
        self._extra_buttons[title] = extra_button
        return extra_button

    def init_status(self):
        self._status = AccordionStatus()
        return self._status

    def init_arrow(self, collapsed):
        self._arrow = Arrow(collapsed=collapsed)
        self._arrow.setStyleSheet("border:0px")

        return self._arrow

    def init_title(self, title=None):
        self._title_label = QtWidgets.QLabel(title)
        self._title_label.setStyleSheet("border:0px")

        return self._title_label

    def init_checkbox(self, checked, enabled):
        self._checkbox = QtWidgets.QCheckBox()
        self._checkbox.setChecked(checked)
        self._checkbox.setEnabled(enabled)
        return self._checkbox

    def mousePressEvent(self, event):
        self.clicked.emit()
        return super(AccordionTitleWidget, self).mousePressEvent(event)

    def enable_content(self, check_enabled):
        self._title_label.setEnabled(check_enabled)
        self.checked.emit(check_enabled)


class OptionsButton(QtWidgets.QPushButton):

    def __init__(self, title, icon, parent=None):
        super(OptionsButton, self).__init__(parent=parent)
        self.name = title

        self.setMinimumSize(30, 30)
        self.setMaximumSize(30, 30)
        #self.setContentsMargins(0, 0, 0, 0)

        #self.setText(self.name)
        self.setIcon(icon)
        self.setStyleSheet("""
            QPushButton {
                font: 14px;
                text-align: center;
            }
        """)
        self.setFlat(True)

        self.build()
        self.post_build()

    def build(self):
        self.main_widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout()
        self.main_widget.setLayout(layout)
        self.main_widget.layout().setAlignment(QtCore.Qt.AlignTop)
        self.overlay_container = overlay.Overlay(self.main_widget)
        self.overlay_container.setVisible(False)

    def post_build(self):
        self.clicked.connect(self.on_click_callback)

    def on_click_callback(self):
        main_window = utils.get_main_framework_window_from_widget(self)
        if main_window:
            self.overlay_container.setParent(main_window)
        self.overlay_container.setVisible(True)

    def add_validator_widget(self, widget):
        self.main_widget.layout().addWidget(QtWidgets.QLabel(''))
        self.main_widget.layout().addWidget(QtWidgets.QLabel(''))
        self.main_widget.layout().addWidget(QtWidgets.QLabel('<html><strong>Validators:<strong><html>'))
        self.main_widget.layout().addWidget(widget)

    def add_output_widget(self, widget):
        self.main_widget.layout().addWidget(QtWidgets.QLabel(''))
        self.main_widget.layout().addWidget(QtWidgets.QLabel('<html><strong>Output:<strong><html>'))
        self.main_widget.layout().addWidget(widget)

class AccordionStatus(QtWidgets.QLabel):
    # #: Unknown status of plugin execution.
    # UNKNOWN_STATUS = 'UNKONWN_STATUS'
    # #: Succed status of plugin execution.
    # SUCCESS_STATUS = 'SUCCESS_STATUS'
    # #: Warning status of plugin execution.
    # WARNING_STATUS = 'WARNING_STATUS'
    # #: Error status of plugin execution.
    # ERROR_STATUS = 'ERROR_STATUS'
    # #: Exception status of plugin execution.
    # EXCEPTION_STATUS = 'EXCEPTION_STATUS'
    # #: Running status of plugin execution.
    # RUNNING_STATUS = 'RUNNING_STATUS'
    # #: Default status of plugin execution.
    # DEFAULT_STATUS = 'PAUSE_STATUS'
    status_icons = constants.icons.status_icons

    def __init__(self, parent=None):
        super(AccordionStatus, self).__init__(parent=parent)
        #icon = self.status_icons[constants.DEFAULT_STATUS]
        icon = qta.icon('mdi6.check', color='gray')
        self.setAlignment(QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter)
        self.setPixmap(icon.pixmap(QtCore.QSize(16,16)))

    def set_status(self, status, message=None):
        #icon = self.status_icons[status]
        icon = qta.icon('mdi6.check', color='gray')
        self.setPixmap(icon.pixmap(QtCore.QSize(16,16)))
        if message:
            self.setToolTip(str(message))

class AccordionArrowContainer(QtWidgets.QWidget):
    def __init__(self, parent=None, collapsed=False):
        super(AccordionArrowContainer, self).__init__(parent=parent)
        self.setLayout(QtWidgets.QHBoxLayout())
        self.set_arrow(int(collapsed))

    def set_arrow(self, arrow_direction):
        for i in reversed(range(self.layout().count())):
            self.layout().itemAt(i).widget().setParent(None)
        if arrow_direction:
            self.layout().addWidget(QtWidgets.QLabel(qta.icon('mdi6.chevron-down', color='gray')))
        else:
            self.layout().addWidget(QtWidgets.QLabel(qta.icon('mdi6.chevron-up', color='gray')))

class Arrow(QtWidgets.QFrame):
    def __init__(self, parent=None, collapsed=False):
        super(Arrow, self).__init__(parent=parent)

        self.setMinimumSize(24, 24)
        self.setMaximumSize(24, 24)

        # horizontal == 0
        self._arrow_horizontal = QtGui.QPolygonF().fromList(
            [
                QtCore.QPointF(7.0, 8.0),
                QtCore.QPointF(17.0, 8.0),
                QtCore.QPointF(12.0, 13.0)
            ]
        )
        # vertical == 1
        self._arrow_vertical = QtGui.QPolygonF().fromList(
            [
                QtCore.QPointF(8.0, 7.0),
                QtCore.QPointF(13.0, 12.0),
                QtCore.QPointF(8.0, 17.0)
            ]
        )
        # arrow
        self._arrow = None
        self.set_arrow(int(collapsed))

    def set_arrow(self, arrow_dir):
        if arrow_dir:
            self._arrow = self._arrow_vertical
        else:
            self._arrow = self._arrow_horizontal
        self.update()

    def paintEvent(self, event):
        painter = QtGui.QPainter()
        painter.begin(self)
        painter.setBrush(QtGui.QColor(192, 192, 192))
        painter.setPen(QtGui.QColor(64, 64, 64))
        painter.drawPolygon(self._arrow)
        painter.end()