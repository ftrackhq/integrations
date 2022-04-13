# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

from Qt import QtGui, QtWidgets

from functools import partial
from ftrack_connect_pipeline import constants as pipeline_constants
from ftrack_connect_pipeline_qt import constants
from ftrack_connect_pipeline_qt.plugin.widgets import BaseOptionsWidget
from ftrack_connect_pipeline_qt.ui.client import BaseUIWidget
from ftrack_connect_pipeline_qt.ui.client.default import (
    DefaultStepContainerWidget,
)
from ftrack_connect_pipeline_qt.ui.utility.widget.accordion import (
    AccordionWidget,
)
from ftrack_connect_pipeline_qt.ui.utility.widget.base.accordion_base import (
    AccordionBaseWidget,
)
from ftrack_connect_pipeline_qt.ui.utility.widget import group_box


class GroupBoxStepContainerWidget(BaseUIWidget):
    '''Widget representation of a boolean'''

    def __init__(self, name, fragment_data, parent=None):
        '''Initialise JsonBoolean with *name*, *schema_fragment*,
        *fragment_data*, *previous_object_data*, *widget_factory*, *parent*'''

        super(GroupBoxStepContainerWidget, self).__init__(
            name, fragment_data, parent=parent
        )

    def build(self):
        self._widget = group_box.GroupBox(self.name, parent=self.parent)
        main_layout = QtWidgets.QVBoxLayout()
        self.widget.setLayout(main_layout)


class AccordionStepContainerWidget(BaseUIWidget):
    '''Widget representation of a boolean'''

    def __init__(self, name, fragment_data, parent=None):
        '''Initialise JsonBoolean with *name*, *schema_fragment*,
        *fragment_data*, *previous_object_data*, *widget_factory*, *parent*'''

        super(AccordionStepContainerWidget, self).__init__(
            name, fragment_data, parent=parent
        )

    def build(self):
        self._widget = AccordionWidget(
            title="{}: 0 components selected".format(self._name),
            checkable=False,
            collapsed=False,
            parent=self.parent,
        )

    def update_selected_components(self, enabled, total):
        self._widget._title_frame._title_label.setText(
            "{}: {} of {} components selected".format(
                self._name, enabled, total
            )
        )

    def parent_widget(self, step_widget):
        if self.widget:
            widget = (
                step_widget.widget
                if isinstance(step_widget, BaseUIWidget)
                else step_widget
            )
            self.widget.add_widget(widget)
            if isinstance(widget, AccordionBaseWidget):
                widget.setVisible(True)
        else:
            self.logger.error("Please create a widget before parent")


class TabStepContainerWidget(DefaultStepContainerWidget):
    '''Widget representation of a boolean'''

    def __init__(self, name, fragment_data, parent=None):
        '''Initialise JsonBoolean with *name*, *schema_fragment*,
        *fragment_data*, *previous_object_data*, *widget_factory*, *parent*'''

        self.status_icons = constants.icons.status_icons
        self._inner_widget_status = {}

        super(TabStepContainerWidget, self).__init__(
            name, fragment_data, parent=parent
        )

    def build(self):
        super(TabStepContainerWidget, self).build()
        self.tab_widget = QtWidgets.QTabWidget(parent=self.parent)
        self.checkBoxList = []
        self.widget.layout().addWidget(self.tab_widget)

    def parent_widget(self, step_widget):
        if self.tab_widget:
            tab_idx = 0
            widget = None
            icon = self.status_icons[constants.DEFAULT_STATUS]
            if isinstance(step_widget, BaseUIWidget):
                tab_idx = self.tab_widget.addTab(
                    step_widget.widget, QtGui.QIcon(icon), step_widget.name
                )
                widget = step_widget.widget
            else:
                tab_idx = self.tab_widget.addTab(
                    step_widget, QtGui.QIcon(icon), step_widget.name
                )
                widget = step_widget
            # Connect status of the widget
            inner_widgets = widget.findChildren(BaseOptionsWidget)
            for inner_widget in inner_widgets:
                inner_widget.statusUpdated.connect(
                    partial(self.update_inner_status, inner_widget, tab_idx)
                )

            # Add checkbox for the optional components
            if isinstance(step_widget, BaseUIWidget):
                if step_widget.is_optional:
                    checkbox = QtWidgets.QCheckBox()
                    checkbox.setChecked(True)
                    self.checkBoxList.append(checkbox)
                    self.tab_widget.tabBar().setTabButton(
                        tab_idx, QtWidgets.QTabBar.RightSide, checkbox
                    )
                    checkbox.stateChanged.connect(
                        partial(self._toggle_tab_state, tab_idx, step_widget)
                    )
            if isinstance(widget, AccordionBaseWidget):
                widget.setVisible(True)
        else:
            self.logger.error("Please create a widget before parent")

    def _toggle_tab_state(self, tab_idx, step_widget, check_state):
        if check_state == 0:
            self.tab_widget.setTabEnabled(tab_idx, False)
            step_widget.set_enabled(False)
            return
        self.tab_widget.setTabEnabled(tab_idx, True)
        step_widget.set_enabled(True)

    def update_inner_status(self, inner_widget, tab_idx, data):
        status, message = data

        self._inner_widget_status[inner_widget] = status

        all_bool_status = [
            pipeline_constants.status_bool_mapping[_status]
            for _status in list(self._inner_widget_status.values())
        ]
        if all(all_bool_status):
            icon = self.status_icons[constants.SUCCESS_STATUS]
            self.tab_widget.setTabIcon(tab_idx, QtGui.QIcon(icon))
        else:
            if constants.RUNNING_STATUS in list(
                self._inner_widget_status.values()
            ):
                icon = self.status_icons[constants.RUNNING_STATUS]
                self.tab_widget.setTabIcon(tab_idx, QtGui.QIcon(icon))
            else:
                icon = self.status_icons[constants.ERROR_STATUS]
                self.tab_widget.setTabIcon(tab_idx, QtGui.QIcon(icon))


class ComboBoxStepContainerWidget(BaseUIWidget):
    '''Widget representation of a boolean'''

    def __init__(self, name, fragment_data, parent=None):
        '''Initialise JsonBoolean with *name*, *schema_fragment*,
        *fragment_data*, *previous_object_data*, *widget_factory*, *parent*'''

        super(ComboBoxStepContainerWidget, self).__init__(
            name, fragment_data, parent=parent
        )

    def build(self):
        self._widget = QtWidgets.QComboBox()

    def update_selected_components(self, enabled, total):
        pass

    def parent_widget(self, step_widget):
        if self.widget:
            self.widget.addItem(step_widget.get_label())
            # Assume ComboBoxItemStepWidget
            step_widget.set_parent(self)
        else:
            self.logger.error("Please create a widget before parent")


class RadioButtonStepContainerWidget(BaseUIWidget):
    '''Widget representation of a boolean'''

    def __init__(self, name, fragment_data, parent=None):
        '''Initialise JsonBoolean with *name*, *schema_fragment*,
        *fragment_data*, *previous_object_data*, *widget_factory*, *parent*'''

        super(RadioButtonStepContainerWidget, self).__init__(
            name, fragment_data, parent=parent
        )

    def pre_build(self):
        self._widget = QtWidgets.QWidget()
        self.widget.setLayout(QtWidgets.QVBoxLayout())
        self.button_group = QtWidgets.QButtonGroup(self._widget)

    def parent_widget(self, widget):
        super(RadioButtonStepContainerWidget, self).parent_widget(widget)
        self.button_group.addButton(widget.button)

    def pre_select(self):
        for button in self.button_group.buttons():
            if button.isEnabled():
                button.setChecked(True)
                break
