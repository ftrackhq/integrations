# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

import logging
from functools import partial
from ftrack_connect_pipeline import constants as pipeline_constants
from ftrack_connect_pipeline_qt import constants
from ftrack_connect_pipeline_qt.client.widgets.options import BaseOptionsWidget
from ftrack_connect_pipeline_qt.client.widgets.client_ui import BaseUIWidget
from ftrack_connect_pipeline_qt.client.widgets.client_ui.default.step_container import DefaultStepContainerWidget
from ftrack_connect_pipeline_qt.ui.utility.widget.accordion import AccordionWidget
from Qt import QtGui, QtCore, QtWidgets


class GroupBoxStepContainerWidget(BaseUIWidget):
    '''Widget representation of a boolean'''
    def __init__(self, name, fragment_data, parent=None):
        '''Initialise JsonBoolean with *name*, *schema_fragment*,
        *fragment_data*, *previous_object_data*, *widget_factory*, *parent*'''

        super(GroupBoxStepContainerWidget, self).__init__(
            name, fragment_data, parent=parent
        )

    def build(self):
        self._widget = QtWidgets.QGroupBox(self.name)
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
            title="0 coomponents selected", checkable=False
        )

    def parent_widget(self, step_widget):
        if self.widget:
            if hasattr(step_widget, 'widget'):
                self.widget.add_widget(step_widget.widget)
            else:
                self.widget.add_widget(step_widget)
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
        self.tab_widget = QtWidgets.QTabWidget()
        self.checkBoxList = []
        self.widget.layout().addWidget(self.tab_widget)

    def parent_widget(self, step_widget):
        if self.tab_widget:
            tab_idx = 0
            widget = None
            icon = self.status_icons[constants.DEFAULT_STATUS]
            if hasattr(step_widget, 'widget'):
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
                inner_widget.status_updated.connect(
                    partial(self.update_inner_status, inner_widget, tab_idx)
                )

            # Add checkbox for the optional components
            if hasattr(step_widget, 'is_optional'):
                if step_widget.is_optional:
                    checkbox = QtWidgets.QCheckBox()
                    checkbox.setChecked(True)
                    self.checkBoxList.append(checkbox)
                    self.tab_widget.tabBar().setTabButton(
                        tab_idx,
                        QtWidgets.QTabBar.RightSide,
                        checkbox
                    )
                    checkbox.stateChanged.connect(
                        partial(self._toggle_tab_state, tab_idx, step_widget)
                    )
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
            if constants.RUNNING_STATUS in list(self._inner_widget_status.values()):
                icon = self.status_icons[constants.RUNNING_STATUS]
                self.tab_widget.setTabIcon(tab_idx, QtGui.QIcon(icon))
            else:
                icon = self.status_icons[constants.ERROR_STATUS]
                self.tab_widget.setTabIcon(tab_idx, QtGui.QIcon(icon))

