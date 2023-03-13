# :coding: utf-8
# :copyright: Copyright (c) 2014-2021 ftrack
from functools import partial

from Qt import QtCore, QtWidgets

from ftrack_connect_pipeline_qt.ui.factory.base import BaseUIWidgetObject
from ftrack_connect_pipeline_qt.ui.utility.widget.base.accordion_base import (
    AccordionBaseWidget,
)
from ftrack_connect_pipeline_qt.plugin.widget.load_widget import (
    LoadBaseWidget,
)
from ftrack_connect_pipeline_qt.ui.utility.widget import line
from ftrack_connect_pipeline_qt.ui.utility.widget import overlay
from ftrack_connect_pipeline_qt import utils
from ftrack_connect_pipeline_qt.ui.utility.widget import icon, scroll_area
from ftrack_connect_pipeline_qt.plugin.widget import BaseOptionsWidget
from ftrack_connect_pipeline_qt.ui.utility.widget.accordion import (
    AccordionWidget,
)
from ftrack_connect_pipeline_qt.ui.utility.widget.button import OptionsButton


def recursive_get_load_mode_container(widget):
    '''Recursively search layout of *widget* and locate a widget inheriting from :class: `ftrack_connect_pipeline_qt.plugin.widgets.load_widget.LoadBaseWidget`'''
    if not widget.layout():
        return
    for idx in range(0, widget.layout().count()):
        inner_item = widget.layout().itemAt(idx)
        if inner_item and inner_item.widget():
            if isinstance(inner_item.widget(), LoadBaseWidget):
                return inner_item.widget()
            else:
                load_mode_widget = recursive_get_load_mode_container(
                    inner_item.widget()
                )
                if load_mode_widget:
                    return load_mode_widget
    return None


class PublisherOptionsButton(OptionsButton):
    '''Options button on publisher accordion'''

    def __init__(self, title, icon, parent=None):
        '''
        Initialize options button

        :param title: The name of the step (component)
        :param icon: The button icon to use
        :param parent: the parent dialog or frame
        '''
        super(PublisherOptionsButton, self).__init__(parent=parent)
        self._name = title
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
        self.main_widget = QtWidgets.QFrame()
        self.main_widget.setLayout(QtWidgets.QVBoxLayout())
        self.main_widget.layout().setAlignment(QtCore.Qt.AlignTop)

        title_label = QtWidgets.QLabel(self._name)
        title_label.setObjectName('h2')
        self.main_widget.layout().addWidget(title_label)
        self.main_widget.layout().addWidget(QtWidgets.QLabel(''))

        self._component_options_widget = QtWidgets.QWidget()
        self._component_options_widget.setLayout(QtWidgets.QVBoxLayout())
        self._component_options_widget.layout().addWidget(
            QtWidgets.QLabel(''), 100
        )  # spacer

        scroll = scroll_area.ScrollArea()
        scroll.setWidget(self._component_options_widget)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)

        self.main_widget.layout().addWidget(scroll)
        self.overlay_container = overlay.Overlay(
            self.main_widget,
            height_percentage=0.9,
            transparent_background=False,
        )
        self.overlay_container.setVisible(False)

    def post_build(self):
        self.clicked.connect(self.on_click_callback)

    def on_click_callback(self):
        '''Callback on clicking the options button, show the publish options overlay'''
        main_window = utils.get_main_framework_window_from_widget(self)
        if main_window:
            self.overlay_container.setParent(main_window)
        self.overlay_container.setVisible(True)

    def add_validator_widget(self, widget):
        '''Add validator plugin container widget to overlay'''
        self._component_options_widget.layout().insertWidget(
            self._component_options_widget.layout().count() - 1, line.Line()
        )
        self._component_options_widget.layout().insertWidget(
            self._component_options_widget.layout().count() - 1,
            QtWidgets.QLabel(''),
        )
        label = QtWidgets.QLabel('Validators:')
        label.setObjectName('gray')
        self._component_options_widget.layout().insertWidget(
            self._component_options_widget.layout().count() - 1, label
        )
        self._component_options_widget.layout().insertWidget(
            self._component_options_widget.layout().count() - 1, widget
        )

    def add_exporter_widget(self, widget):
        '''Add exporter plugin container widget to overlay'''
        self._component_options_widget.layout().insertWidget(
            self._component_options_widget.layout().count() - 1,
            QtWidgets.QLabel(''),
        )
        self._component_options_widget.layout().insertWidget(
            self._component_options_widget.layout().count() - 1, line.Line()
        )
        self._component_options_widget.layout().insertWidget(
            self._component_options_widget.layout().count() - 1,
            QtWidgets.QLabel(''),
        )
        label = QtWidgets.QLabel('Exporter:')
        label.setObjectName('gray')
        self._component_options_widget.layout().insertWidget(
            self._component_options_widget.layout().count() - 1, label
        )
        self._component_options_widget.layout().insertWidget(
            self._component_options_widget.layout().count() - 1, widget
        )


class PublisherAccordionWidget(AccordionBaseWidget):
    '''Accordion widget representation of a publisher schema step (component)'''

    @property
    def options_widget(self):
        return self._options_button

    def __init__(self, parent=None, title=None, checkable=False, checked=True):
        '''
        Initialize the publish accordion

        :param parent: the parent dialog or frame
        :param title: The title of accordion - name of step (component)
        :param checkable: If True, user is allowed the check and un-check accordion
        :param checked: If True, accordion should be checked (enabled) in creation
        '''
        self._input_message = 'Initializing...'
        self._input_status = False
        super(PublisherAccordionWidget, self).__init__(
            AccordionBaseWidget.SELECT_MODE_NONE,
            AccordionBaseWidget.CHECK_MODE_CHECKBOX
            if checkable
            else AccordionBaseWidget.CHECK_MODE_CHECKBOX_DISABLED,
            checked=checked,
            title=title,
            parent=parent,
        )

    def init_status_label(self):
        self._status_label = QtWidgets.QLabel()
        self._status_label.setObjectName('color-primary')
        return self._status_label

    def init_options_button(self):
        '''Create widget representing publisher options'''
        self._options_button = PublisherOptionsButton(
            self.title, icon.MaterialIcon('settings', color='gray')
        )
        self._options_button.setObjectName('borderless')
        return self._options_button

    def init_status_icon(self):
        '''Create widget representing publish status'''
        self._status_icon = icon.MaterialIconWidget('check')
        self._status_icon.setObjectName('borderless')
        return self._status_icon

    def init_header_content(self, header_widget, collapsed):
        '''(Override) Add publish related widgets to the accordion header'''
        header_layout = QtWidgets.QHBoxLayout()
        header_widget.setLayout(header_layout)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(0)
        header_layout.addWidget(self.init_status_label())
        header_layout.addStretch()
        header_layout.addWidget(line.Line(horizontal=True))
        header_layout.addWidget(self.init_options_button())
        header_layout.addWidget(line.Line(horizontal=True))
        header_layout.addWidget(self.init_status_icon())

    def add_widget(self, widget):
        '''(Override)'''
        super(PublisherAccordionWidget, self).add_widget(widget)
        self._connect_inner_widgets(widget)

    def post_build(self):
        self.update_input(self._input_message, self._input_status)
        super(PublisherAccordionWidget, self).post_build()
        self.header.title_label.setObjectName('h3')

    def _connect_inner_widgets(self, widget):
        if issubclass(widget.__class__, BaseOptionsWidget):
            self._widgets[widget] = widget
            return
        inner_widgets = widget.findChildren(BaseOptionsWidget)
        self._widgets[widget] = inner_widgets

    def on_collapse(self, collapsed):
        '''Callback on accordion collapse/expand.'''
        self.update_input(self._input_message, self._input_status)

    def update_input(self, message, status):
        '''Update the status label and icon'''
        self._input_message = message
        self._input_status = status
        if self.collapsed:
            self._status_label.setText(' - {}'.format(self._input_message))
        else:
            self._status_label.setText('')
        visibility = not status is None
        if self._status_icon.isVisible() != visibility:
            self._status_icon.setVisible(visibility)
        if not status is None:
            self._status_icon.set_icon(
                'check' if status else 'error_outline',
                color='gray'
                if not self.checked
                else ('green' if status else 'orange'),
            )


class AccordionStepWidgetObject(BaseUIWidgetObject):
    '''Accordion widget representation of a schema step (component)'''

    def __init__(self, name, fragment_data, parent=None):
        '''Initialise AccordionStepWidgetObject with *name*,
        *fragment_data* and *parent*'''

        super(AccordionStepWidgetObject, self).__init__(
            name, fragment_data, parent=parent
        )

    def build(self):
        self._widget = AccordionWidget(
            title="{}".format(self._name),
            checkable=self.optional,
            checked=self.enabled,
            collapsable=False,
        )
        self._widget.content.layout().setContentsMargins(0, 10, 0, 0)

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


class PublisherAccordionStepWidgetObject(BaseUIWidgetObject):
    '''Widget representation of a boolean'''

    @property
    def enabled(self):
        '''(Redefine) Return True if widget is enabled as evaluated from schema'''
        if self._widget:
            return self._widget.checked
        else:
            return self._is_enabled

    @property
    def options_widget(self):
        return self.widget.options_widget

    def __init__(self, name, fragment_data, parent=None):
        '''Initialise PublisherAccordionStepWidgetObject with *name*,
        *fragment_data* and *parent*'''

        super(PublisherAccordionStepWidgetObject, self).__init__(
            name, fragment_data, parent=parent
        )

    def build(self):
        self._widget = PublisherAccordionWidget(
            title=self.name, checkable=self.optional, checked=self.enabled
        )

    def parent_validator(self, step_widget):
        '''(Override)'''
        if self.options_widget:
            if isinstance(step_widget, BaseUIWidgetObject):
                self.options_widget.add_validator_widget(step_widget.widget)
            else:
                self.options_widget.add_validator_widget(step_widget)
        else:
            self.logger.error("Please create a options_widget before parent")

    def parent_exporter(self, step_widget):
        '''(Override)'''
        if self.options_widget:
            if isinstance(step_widget, BaseUIWidgetObject):
                self.options_widget.add_exporter_widget(step_widget.widget)
            else:
                self.options_widget.add_exporter_widget(step_widget)
        else:
            self.logger.error("Please create a options_widget before parent")

    def set_output_plugin_name(self, plugin_name):
        self.widget.setToolTip('({}) {}'.format(plugin_name, self.description))

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

    def collector_input_changed(self, input):
        '''The collector input has changed, update accordion'''
        input_info = input.get('message') or ''
        input_status = input.get('status') or False
        self._widget.update_input(input_info, input_status)

    def to_json_object(self):
        '''(Override)'''
        out = {}
        out['enabled'] = self.enabled
        return out


class LoaderStepWidgetObject(BaseUIWidgetObject):
    '''Widget representation of a loader options schema step (component)'''

    def __init__(self, name, fragment_data, parent=None):
        '''Initialise LoaderStepWidgetObject with *name*,
        *fragment_data* and *parent*'''

        super(LoaderStepWidgetObject, self).__init__(
            name, fragment_data, parent=parent
        )

    def build(self):
        self._widget = QtWidgets.QWidget()
        self._widget.setLayout(QtWidgets.QVBoxLayout())
        title_label = QtWidgets.QLabel(self._name)
        title_label.setObjectName('h2')
        self._widget.layout().addWidget(title_label)
        self._widget.layout().addWidget(QtWidgets.QLabel(''))


class RadioButtonStepWidgetObject(BaseUIWidgetObject):
    '''Radio button widget representation of a schema step (component)'''

    @property
    def enabled(self):
        '''(Redefine) Return True if widget is enabled as evaluated from schema'''
        return self._button.isChecked()

    @enabled.setter
    def enabled(self, enabled):
        '''(Redefine) Set widget enable property'''
        self._is_enabled = enabled
        self.button.setEnabled(enabled)
        self.button.setText(self.get_label())

    @property
    def available(self):
        '''Return true if widget is available'''
        return self._button and self._button.isEnabled()

    @available.setter
    def available(self, value):
        '''Set widget available property to *value*'''
        if value:
            self.enabled = True
        else:
            self.enabled = False
            if self.button.isChecked():
                self.button.setChecked(False)

    @property
    def button(self):
        '''Return the radio button widget'''
        return self._button

    def __init__(self, name, fragment_data, parent=None):
        '''Initialise JsonBoolean with *name*, *schema_fragment*,
        *fragment_data*, *previous_object_data*, *widget_factory*, *parent*'''
        super(RadioButtonStepWidgetObject, self).__init__(
            name, fragment_data, parent=parent
        )
        self._unavailable_reason = ''
        self._component = None

    def build(self):
        self._button = QtWidgets.QRadioButton(self.name)
        self._widget = QtWidgets.QWidget()
        self._widget.setLayout(QtWidgets.QHBoxLayout())
        self._widget.layout().addWidget(self.button)

    def post_build(self):
        self.widget.layout().setContentsMargins(2, 2, 2, 2)

    def check_components(self, session, components, file_formats=None):
        '''Set available property based on *components*'''
        self._component = None
        self._session = session
        for component in components:
            if component['name'] == self.name:
                self._component = component
                break
        if not self._component:
            self.available = False
            self._unavailable_reason = ''
            return False
        else:
            if (
                file_formats is None
                or self._component['file_type'] in file_formats
            ):
                self.available = True
            else:
                self.available = False
                self._unavailable_reason = 'Cannot open this format.'
            return True

    def get_label(self):
        '''Return the label for parent combobox'''
        result = '{}'.format(self.name)
        if self.available and self._component:
            # Fetch path
            try:
                location = self._session.pick_location()
                # Is component in this location
                if (
                    location.get_component_availability(self._component)
                    == 100.0
                ):
                    self.button.setToolTip(
                        location.get_filesystem_path(self._component)
                    )
                else:
                    self.available = False
                    self._unavailable_reason = (
                        'Missing in this location ({})'.format(
                            location['name']
                        )
                    )
            except Exception as e:
                self.widget.setToolTip(str(e))
        if len(self._unavailable_reason or '') > 0:
            result += ': {}'.format(self._unavailable_reason)
        return result

    def to_json_object(self):
        '''(Override)'''
        out = {}
        out['enabled'] = self.available and self.enabled
        return out
