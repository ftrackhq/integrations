# :coding: utf-8
# :copyright: Copyright (c) 2014-2021 ftrack
from functools import partial

import qtawesome as qta

from Qt import QtCore, QtWidgets

from ftrack_connect_pipeline_qt import constants
from ftrack_connect_pipeline import constants as pipeline_constants
from ftrack_connect_pipeline_qt.ui.client import BaseUIWidget
from ftrack_connect_pipeline_qt.ui.utility.widget.base.accordion_base import  AccordionBaseWidget
from ftrack_connect_pipeline_qt.ui.client.default.step_widget import DefaultStepWidget
from ftrack_connect_pipeline_qt.plugin.widgets.load_widget import LoadBaseWidget
from ftrack_connect_pipeline_qt.ui.utility.widget import line
from ftrack_connect_pipeline_qt.ui.utility.widget import overlay
from ftrack_connect_pipeline_qt import utils
from ftrack_connect_pipeline_qt.ui.utility.widget.material_icon import MaterialIconWidget
from ftrack_connect_pipeline_qt.plugin.widgets import BaseOptionsWidget

def recursive_get_load_mode_container(widget):
    if not widget.layout():
        return
    load_mode_widget = None
    for idx in range(0, widget.layout().count()):
        inner_item = widget.layout().itemAt(idx)
        if inner_item and inner_item.widget():
            if isinstance(inner_item.widget(), LoadBaseWidget):
                return inner_item.widget()
            else:
                load_mode_widget = recursive_get_load_mode_container(inner_item.widget())
                if load_mode_widget:
                    return load_mode_widget
    return load_mode_widget

class OptionsButton(QtWidgets.QPushButton):

    def __init__(self, title, icon, parent=None):
        super(OptionsButton, self).__init__(parent=parent)
        self.name = title
        self._icon = icon

        self.pre_build()
        self.build()
        self.post_build()

    def pre_build(self):
        self.setMinimumSize(30, 30)
        self.setMaximumSize(30, 30)
        self.setIcon(self._icon)
        self.setFlat(True)

    def build(self):
        self.main_widget = QtWidgets.QWidget()
        self.main_widget.setLayout(QtWidgets.QVBoxLayout())
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


class PublisherAccordion(AccordionBaseWidget):

    @property
    def options_widget(self):
        return self._options_button

    def __init__(self, parent=None, title=None, checkable=False):
        super(PublisherAccordion,self).__init__(AccordionBaseWidget.SELECT_MODE_NONE,
            AccordionBaseWidget.CHECK_MODE_CHECKBOX if checkable else AccordionBaseWidget.CHECK_MODE_CHECKBOX_DISABLED,
            title=title, parent=parent)

    def init_status_label(self):
        self._status_label = QtWidgets.QLabel()
        self._status_label.setObjectName('purple')
        return self._status_label

    def init_options_button(self):
        self._options_button = OptionsButton('O', qta.icon('mdi6.cog',color='gray'))
        self._options_button.setObjectName('borderless')
        return self._options_button

    def init_status_icon(self):
        self._status_icon = MaterialIconWidget('check')
        self._status_icon.setObjectName('borderless')
        return self._status_icon

    def init_header_content(self,layout, collapsed):
        '''Add publish related widgets to the accordion header'''
        layout.addWidget(self.init_status_label())
        layout.addStretch()
        layout.addWidget(line.Line(horizontal=True))
        layout.addWidget(self.init_options_button())
        layout.addWidget(line.Line(horizontal=True))
        layout.addWidget(self.init_status_icon())

    def add_widget(self, widget):
        super(PublisherAccordion, self).add_widget(widget)
        self._connect_inner_widgets(widget)

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

    def on_collapse(self, collapsed):
        '''Callback on accordion collapse/expand.'''
        self.update_input(self._input_message, self._input_status)

    def update_input(self, message, status):
        '''(Override)'''
        self._input_message = message
        self._input_status = status
        if self.collapsed:
            self._status_label.setText('- {}'.format(self._input_message))
        else:
            self._status_label.setText('')
        self._status_icon.setVisible(not status is None)
        if not status is None:
            self._status_icon.set_icon('check' if status else 'alert-circle-outline',
                color = 'gray' if not self.checkable or not self.checked else
                    ('green' if status else 'orange'))


class AccordionStepWidget(BaseUIWidget):
    '''Widget representation of a boolean'''

    @property
    def is_enabled(self):
        if self._widget:
            return self._widget.checked
        else:
            return self._is_enabled

    @property
    def options_widget(self):
        return self.widget.options_widget

    def __init__(self, name, fragment_data, parent=None):
        '''Initialise JsonBoolean with *name*, *schema_fragment*,
        *fragment_data*, *previous_object_data*, *widget_factory*, *parent*'''

        super(AccordionStepWidget, self).__init__(
            name, fragment_data, parent=parent
        )

    def pre_build(self):
        self._is_optional = self.fragment_data.get('optional')

    def build(self):
        self._widget = PublisherAccordion(
            title=self.name, checkable=self.is_optional
        )

    def parent_validator(self, step_widget):
        if self.options_widget:
            if isinstance(step_widget, BaseUIWidget):
                self.options_widget.add_validator_widget(step_widget.widget)
            else:
                self.options_widget.add_validator_widget(step_widget)
        else:
            self.logger.error("Please create a options_widget before parent")

    def parent_output(self, step_widget):
        if self.options_widget:
            if isinstance(step_widget, BaseUIWidget):
                self.options_widget.add_output_widget(step_widget.widget)
            else:
                self.options_widget.add_output_widget(step_widget)
        else:
            self.logger.error("Please create a options_widget before parent")

    def parent_widget(self, step_widget):
        '''Override'''
        if self.widget:
            if isinstance(step_widget, BaseUIWidget):
                self.widget.add_widget(step_widget.widget)
            else:
                self.widget.add_widget(step_widget)
        else:
            self.logger.error("Please create a widget before parent")

    def collector_input_changed(self, input):
        '''The collector input has changed, update accordion'''
        input_info = input.get('message') or ''
        input_status = input.get('status') or False
        self._widget.update_input(input_info, input_status)

    def to_json_object(self):
        '''Return a formated json with the data from the current widget'''
        out = {}
        out['enabled'] = self.is_enabled
        return out


class OptionsStepWidget(DefaultStepWidget):
    '''Widget representation of a boolean'''

    @property
    def options_widget(self):
        return self._options_widget

    def __init__(self, name, fragment_data, parent=None):
        '''Initialise JsonBoolean with *name*, *schema_fragment*,
        *fragment_data*, *previous_object_data*, *widget_factory*, *parent*'''

        self._options_widget = None

        super(OptionsStepWidget, self).__init__(
            name, fragment_data, parent=parent
        )

    def build(self):
        super(OptionsStepWidget, self).build()
        self.show_options_button = QtWidgets.QPushButton("Show options")

        self._options_widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout()
        self.options_widget.setLayout(layout)

        self.widget.layout().addWidget(self.show_options_button )
        self.widget.layout().addWidget(self.options_widget)
        self.options_widget.hide()

    def post_build(self):
        self.show_options_button.clicked.connect(self.toggle_options)

    def toggle_options(self):
        if self.options_widget.isVisible():
            self.options_widget.hide()
            self.show_options_button.setText("Show options")
        else:
            self.options_widget.show()
            self.show_options_button.setText("Hide options")

    def parent_options(self, stage_widget):
        if self.options_widget:
            load_mode_cointainer = None
            if isinstance(stage_widget, BaseUIWidget):
                self.options_widget.layout().addWidget(stage_widget.widget)
                load_mode_cointainer = recursive_get_load_mode_container(stage_widget.widget)
            else:
                self.options_widget.layout().addWidget(stage_widget)
                load_mode_cointainer = recursive_get_load_mode_container(stage_widget.widget)
            if load_mode_cointainer:
                mode_layout = load_mode_cointainer.load_mode_layout
                load_mode_cointainer.layout().removeItem(mode_layout)
                self.parent_layout(mode_layout)

        else:
            self.logger.error("Please create a options_widget before parent")

    def parent_widget(self, widget):
        if self.widget:
            options_idx = self.widget.layout().indexOf(self.show_options_button)
            if isinstance(widget, BaseUIWidget):
                self.widget.layout().insertWidget((options_idx), widget.widget)
            else:
                self.widget.layout().insertWidget((options_idx), widget)
        else:
            self.logger.error("Please create a widget before parent")

    def parent_layout(self, layout):
        if self.widget:
            options_idx = self.widget.layout().indexOf(self.show_options_button)
            self.widget.layout().insertLayout((options_idx), layout)
        else:
            self.logger.error("Please create a widget before parent")