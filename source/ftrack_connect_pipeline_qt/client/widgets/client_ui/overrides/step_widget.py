from ftrack_connect_pipeline import constants as core_constants
from ftrack_connect_pipeline_qt import constants
from ftrack_connect_pipeline_qt.client.widgets.client_ui import BaseUIWidget
from ftrack_connect_pipeline_qt.ui.utility.widget.accordion import AccordionWidget
from ftrack_connect_pipeline_qt.client.widgets.client_ui.default.step_widget import DefaultStepWidget
from ftrack_connect_pipeline_qt.client.widgets.options.load_widget import LoadBaseWidget
from Qt import QtGui, QtCore, QtWidgets


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

class AccordionStepWidget(BaseUIWidget):
    '''Widget representation of a boolean'''

    @property
    def is_enabled(self):
        if self._widget:
            return self._widget.is_checked()
        else:
            return self._is_enabled

    @property
    def validators_widget(self):
        return self._validators_widget

    @property
    def outputs_widget(self):
        return self._outputs_widget

    def __init__(self, name, fragment_data, parent=None):
        '''Initialise JsonBoolean with *name*, *schema_fragment*,
        *fragment_data*, *previous_object_data*, *widget_factory*, *parent*'''

        self._validators_widget = None
        self._outputs_widget = None

        super(AccordionStepWidget, self).__init__(
            name, fragment_data, parent=parent
        )

    def pre_build(self):
        self._is_optional = self.fragment_data.get('optional')

    def build(self):
        self._widget = AccordionWidget(
            title=self.name, checkable=self.is_optional
        )
        idx=2
        if self.is_optional:
            idx=3

        if core_constants.VALIDATOR in self.fragment_data.get('stage_order'):
            self._validators_widget = self._widget.add_extra_button("V", idx)

        if core_constants.OUTPUT in self.fragment_data.get('stage_order'):
            self._outputs_widget = self._widget.add_extra_button("O", idx)

    def parent_validator(self, step_widget):
        if self.validators_widget:
            if isinstance(step_widget, BaseUIWidget):
                self.validators_widget.add_widget(step_widget.widget)
            else:
                self.validators_widget.add_widget(step_widget)
        else:
            self.logger.error("Please create a validators_widget before parent")

    def parent_output(self, step_widget):
        if self.outputs_widget:
            if isinstance(step_widget, BaseUIWidget):
                self.outputs_widget.add_widget(step_widget.widget)
            else:
                self.outputs_widget.add_widget(step_widget)
        else:
            self.logger.error("Please create a outputs_widget before parent")

    def parent_widget(self, step_widget):
        if self.widget:
            if isinstance(step_widget, BaseUIWidget):
                self.widget.add_widget(step_widget.widget)
            else:
                self.widget.add_widget(step_widget)
        else:
            self.logger.error("Please create a widget before parent")

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