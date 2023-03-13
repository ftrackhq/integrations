# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack
import copy
from functools import partial

from Qt import QtWidgets, QtCore

from ftrack_connect_pipeline.definition.definition_object import DefinitionList

from ftrack_connect_pipeline_qt.plugin.widget import BaseOptionsWidget
from ftrack_connect_pipeline_qt.ui.utility.widget import group_box


class DynamicWidget(BaseOptionsWidget):
    '''Main class to represent a various type of widget based on each type of
    each element of the options dictionary'''

    enable_run_plugin = False

    def __init__(
        self,
        parent=None,
        session=None,
        data=None,
        name=None,
        description=None,
        options=None,
        context_id=None,
        asset_type_name=None,
    ):
        '''initialise DynamicWidget with *parent*, *session*, *data*, *name*,
        *description*, *options*
        '''
        self._type_mapping = {
            str: self._build_str_widget,
            int: self._build_int_widget,
            float: self._build_float_widget,
            list: self._build_list_widget,
            bool: self._build_bool_widget,
        }
        super(DynamicWidget, self).__init__(
            parent=parent,
            session=session,
            data=data,
            name=name,
            description=description,
            options=options,
            context_id=context_id,
            asset_type_name=asset_type_name,
        )

    def _register_widget(self, name, widget):
        '''Register *widget* with *name* and add it to main layout.'''
        if not isinstance(widget, QtWidgets.QCheckBox):
            # Add title label to widget
            widget_layout = QtWidgets.QHBoxLayout()
            widget_layout.setContentsMargins(1, 2, 1, 2)
            widget_layout.setAlignment(QtCore.Qt.AlignTop)
            label = QtWidgets.QLabel(name)

            widget_layout.addWidget(label)
            widget_layout.addWidget(widget)
            self.option_layout.addLayout(widget_layout)
        else:
            # Add widget directly
            self.option_layout.addWidget(widget)

    def _build_str_widget(self, key, value):
        '''build a string widget out of options *key* and *value*'''
        widget = QtWidgets.QLineEdit(str(value))
        self._register_widget(key, widget)
        update_fn = partial(self.set_option_result, key=key)
        widget.textChanged.connect(update_fn)
        self.set_option_result(value, key)

    def _build_int_widget(self, key, value):
        '''build an integer widget out of options *key* and *value*'''
        widget = QtWidgets.QSpinBox()
        widget.setValue(value)
        self._register_widget(key, widget)
        update_fn = partial(self.set_option_result, key=key)
        widget.valueChanged.connect(update_fn)
        self.set_option_result(value, key)

    def _build_float_widget(self, key, value):
        '''build a float widget out of options *key* and *value*'''
        widget = QtWidgets.QDoubleSpinBox()
        widget.setValue(value)
        self._register_widget(key, widget)
        update_fn = partial(self.set_option_result, key=key)
        widget.valueChanged.connect(update_fn)
        self.set_option_result(value, key)

    def _build_bool_widget(self, key, value):
        '''build a bool widget out of options *key* and *value*'''
        widget = QtWidgets.QCheckBox(key)
        widget.setChecked(value)
        self._register_widget(key, widget)
        update_fn = partial(self.set_option_result, key=key, cast_type=bool)
        widget.stateChanged.connect(update_fn)
        self.set_option_result(value, key)

    def _on_current_index_changed(self, widget, key, index):
        value = widget.itemData(index)
        self.set_option_result(value, key=key)

    def _build_list_widget(self, key, values):
        '''build a list widget out of options *key* and *values*'''
        widget = QtWidgets.QComboBox()
        selected_index = 0
        selected_value = None
        for index, item in enumerate(values):
            if isinstance(item, dict):
                widget.addItem(item.get('label', item['value']), item['value'])
                if item.get('default') is True:
                    selected_index = index
                if index == selected_index:
                    selected_value = item['value']
            else:
                # Fall back on standard list of primitives
                widget.addItem(str(item), item)
                if index == selected_index:
                    selected_value = item
        widget.setCurrentIndex(selected_index)
        self._register_widget(key, widget)
        # QComboBox().currentTextChanged only works for PySide2
        widget.currentIndexChanged.connect(
            partial(self._on_current_index_changed, widget, key)
        )
        if selected_value:
            self.set_option_result(selected_value, key)

    def update(self, options, ignore=None):
        '''Combine supplied options from definition, with UI defined options. Ignore the options keys
        provided in *ignore* list, managed by the the child options widget.'''
        # Preprocess, the list values supplied in definitions must override UI defined options
        for key, value in self.options.items():
            if key in (ignore or []):
                continue
            new_value = value
            if isinstance(value, list):
                # Combine, use UI defined option values where we can. Add if not exist.
                new_value = []
                for list_value in value:
                    found_item = None
                    for item in options[key]:
                        if item['value'] == list_value:
                            found_item = item
                            break
                    if found_item:
                        new_value.append(found_item)
                    else:
                        # Add it
                        new_value.append(
                            {
                                'label': str(list_value),
                                'value': str(list_value),
                            }
                        )
                options[key] = new_value
            else:
                # Is it defined as a combobox?
                if key in options and isinstance(options[key], list):
                    new_value = []
                    # Make it present as a combobox and not a string input
                    found = False
                    for item in options[key]:
                        new_value.append(item)
                        if item['value'] == value:
                            found = True
                        elif 'default' in item:
                            del item['default']
                    if not found:
                        # Add it
                        new_value.insert(
                            0,
                            {
                                'label': str(value),
                                'value': str(value),
                                'default': True,
                            },
                        )
            options[key] = new_value
        for key, value in options.items():
            if isinstance(value, list):
                # List/combobox definition, parse
                new_value = []
                supplied_value = self.options.get(key)
                default_item = None
                for item in value:
                    if item is None:
                        item = ''
                    if isinstance(item, str):
                        item = {'label': item, 'value': item}
                    else:
                        item = copy.deepcopy(item)
                    if (
                        supplied_value is not None
                        and item['value'] == supplied_value
                    ):
                        default_item = item
                    elif 'default' in item:
                        if default_item is None:
                            default_item = item
                        del item['default']
                    new_value.append(item)
                # Set the final default item
                if default_item:
                    for item in new_value:
                        if item == default_item:
                            item['default'] = True
                            break
                options[key] = new_value
            else:
                if key in self.options:
                    options[key] = self.options[key]
        # Use the options with UI definitions temporarily until we build
        self.options = options

    def build(self):
        '''build function widgets based on the type of the value of every
        element in the options dictionary'''
        # Create a options group for widgets with a well defined title instead of the default
        self.option_group = group_box.GroupBox(self.get_options_group_name())
        self.option_group.setToolTip(self.description)

        self.option_layout = QtWidgets.QVBoxLayout()
        self.option_group.setLayout(self.option_layout)

        self.layout().addWidget(self.option_group)

        for key, value in list(sorted(self.options.items())):
            # Make sure it is not a hidden/internal framework option, we do not
            # want to expose these within the UI
            if key.find('_') == 0:
                continue
            if isinstance(value, DefinitionList):
                value = value.to_list()
            value_type = type(value)
            widget_fn = self._type_mapping.get(
                value_type, self._build_str_widget
            )
            widget_fn(key, value)

    def get_options_group_name(self):
        '''Return the name of the options group, by default this is the name of the plugin. Can be overridden'''
        return self.name.title()
