# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

from Qt import QtGui, QtWidgets

from ftrack_connect_pipeline_qt.ui.factory.base import BaseUIWidgetObject
from ftrack_connect_pipeline_qt.ui.utility.widget.accordion import (
    AccordionWidget,
)
from ftrack_connect_pipeline_qt.ui.utility.widget import group_box


class GroupBoxStepContainerWidgetObject(BaseUIWidgetObject):
    '''Widget representation of a group box containing schema steps'''

    def __init__(self, name, fragment_data, parent=None):
        '''Initialise GroupBoxStepContainerWidgetObject with *name*,
        *fragment_data* and *parent*'''

        super(GroupBoxStepContainerWidgetObject, self).__init__(
            name, fragment_data, parent=parent
        )

    def build(self):
        self._widget = group_box.GroupBox(self.name)
        main_layout = QtWidgets.QVBoxLayout()
        self.widget.setLayout(main_layout)


class AccordionStepContainerWidgetObject(BaseUIWidgetObject):
    '''Widget representation of a accordion container of schema steps (components)'''

    def __init__(self, name, fragment_data, parent=None):
        '''Initialise JsonBoolean with *name*,
        *fragment_data* and *parent*'''

        super(AccordionStepContainerWidgetObject, self).__init__(
            name, fragment_data, parent=parent
        )

    def build(self):
        self._widget = AccordionWidget(
            title="{}: 0 components selected".format(self._name),
            checkable=False,
            checked=self.enabled,
            collapsed=False,
        )

    def update_selected_components(self, enabled, total):
        '''Update header title according to amount of *enabled* components out of *total*'''
        self._widget._header.title_label.setText(
            "{}: {} of {} components selected".format(
                self._name, enabled, total
            )
        )

    def parent_widget(self, step_widget):
        '''(Override)'''
        if self.widget:
            widget = (
                step_widget.widget
                if isinstance(step_widget, BaseUIWidgetObject)
                else step_widget
            )
            self.widget.add_widget(widget)
        else:
            self.logger.error("Please create a widget before parent")


class ComboBoxStepContainerWidgetObject(BaseUIWidgetObject):
    '''Widget representation of a combobox container of schema steps'''

    def __init__(self, name, fragment_data, parent=None):
        '''Initialise ComboBoxStepContainerWidgetObject with *name*,
        *fragment_data* and *parent*'''

        super(ComboBoxStepContainerWidgetObject, self).__init__(
            name, fragment_data, parent=parent
        )

    def build(self):
        self._widget = QtWidgets.QComboBox()

    def update_selected_components(self, enabled, total):
        pass

    def parent_widget(self, step_widget):
        '''(Override)'''
        if self.widget:
            self.widget.addItem(step_widget.get_label())
            # Assume ComboBoxItemStepWidget
            step_widget.set_parent(self)
        else:
            self.logger.error("Please create a widget before parent")


class RadioButtonStepContainerWidgetObject(BaseUIWidgetObject):
    '''Widget representation of a container of radio button schema steps'''

    def __init__(self, name, fragment_data, parent=None):
        '''Initialise JsonBoolean with *name*,
        *fragment_data* and *parent*'''

        super(RadioButtonStepContainerWidgetObject, self).__init__(
            name, fragment_data, parent=parent
        )

    def pre_build(self):
        self._widget = QtWidgets.QWidget()
        self.widget.setLayout(QtWidgets.QVBoxLayout())
        self.button_group = QtWidgets.QButtonGroup(self._widget)

    def parent_widget(self, widget, add_line=False):
        '''(Override)'''
        super(RadioButtonStepContainerWidgetObject, self).parent_widget(widget)
        self.button_group.addButton(widget.button)

    def pre_select(self):
        for button in self.button_group.buttons():
            if button.isEnabled():
                button.setChecked(True)
                break
