# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

from functools import partial

from Qt import QtCore, QtWidgets, QtGui
from ftrack_connect_pipeline_qt import constants
from ftrack_connect_pipeline import constants as pipeline_constants
from ftrack_connect_pipeline_qt.client.widgets.schema import BaseJsonWidget
from ftrack_connect_pipeline_qt.ui.utility.widget.accordion import AccordionWidget
from ftrack_connect_pipeline_qt.client.widgets.options import BaseOptionsWidget

class StepTabArray(BaseJsonWidget):
    '''
    Override widget representation of an array
    '''

    def __init__(
            self, name, schema_fragment, fragment_data,
            previous_object_data, widget_factory, parent=None
    ):
        '''Initialise StepArray with *name*, *schema_fragment*,
        *fragment_data*, *previous_object_data*, *widget_factory*, *parent*'''

        self.status_icons = constants.icons.status_icons
        self._inner_widget_status = {}

        super(StepTabArray, self).__init__(
            name, schema_fragment, fragment_data, previous_object_data,
            widget_factory, parent=parent
        )

    @property
    def tabs_names(self):
        return self._tabs_names

    def build(self):
        groupBox = QtWidgets.QGroupBox(self.name.capitalize())
        layout = QtWidgets.QVBoxLayout()
        layout.setAlignment(QtCore.Qt.AlignTop)
        groupBox.setLayout(layout)
        groupBox.setFlat(False)
        groupBox.layout().setContentsMargins(0, 0, 0, 0)
        groupBox.setToolTip(self.description)

        self._tabs_names = {}

        if 'items' in self.schema_fragment and self.fragment_data:
            self.tab_widget = QtWidgets.QTabWidget()
            self.checkBoxList = []
            for data in self.fragment_data:
                if type(data) == dict:
                    name = data.get('name')
                    self._type = data.get('type')
                else:
                    name = data

                optional_component = False
                for package in self.widget_factory.package['components']:
                    if package['name'] == name:
                        optional_component = data.get('optional', False)
                        break

                obj = self.widget_factory.create_widget(
                    name, self.schema_fragment['items'], data,
                    self.previous_object_data
                )
                obj.layout().setContentsMargins(0, 0, 0, 0)
                obj.layout().setSpacing(0)


                icon = self.status_icons[constants.DEFAULT_STATUS]
                tab_idx = self.tab_widget.addTab(obj, QtGui.QIcon(icon), name)

                self._tabs_names[name] = tab_idx

                inner_widgets = obj.findChildren(BaseOptionsWidget)
                for inner_widget in inner_widgets:
                    inner_widget.status_updated.connect(
                        partial(self.update_inner_status, inner_widget, tab_idx)
                    )

                if optional_component:
                    checkbox = QtWidgets.QCheckBox()
                    checkbox.setChecked(True)
                    self.checkBoxList.append(checkbox)
                    self.tab_widget.tabBar().setTabButton(
                        tab_idx,
                        QtWidgets.QTabBar.RightSide,
                        checkbox
                    )
                    checkbox.stateChanged.connect(
                        lambda check_state: self._toggle_tab_state(
                            tab_idx, check_state
                        )
                    )
                # self.tab_widget.setTabPosition(QtWidgets.QTabWidget.West)

            groupBox.layout().addWidget(self.tab_widget)
        self.layout().setContentsMargins(0, 0, 0, 0)

        self.layout().addWidget(groupBox)

    def _toggle_tab_state(self, tab_idx, check_state):
        if check_state == 0:
            self.tab_widget.setTabEnabled(tab_idx, False)
            return
        self.tab_widget.setTabEnabled(tab_idx, True)

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

    def to_json_object(self):
        out = []
        for idx in range(0, self.tab_widget.count()):
            widget = self.tab_widget.widget(idx)
            if 'to_json_object' in dir(widget):
                data = widget.to_json_object()
                data['enabled'] = self.tab_widget.isTabEnabled(idx)
                out.append(data)
        return out


class StepAccordionArray(BaseJsonWidget):
    '''
    Override widget representation of an array
    '''

    @property
    def accordion_widgets(self):
        return self._accordion_widgets

    def __init__(
            self, name, schema_fragment, fragment_data,
            previous_object_data, widget_factory, parent=None
    ):
        '''Initialise StepArray with *name*, *schema_fragment*,
        *fragment_data*, *previous_object_data*, *widget_factory*, *parent*'''
        super(StepAccordionArray, self).__init__(
            name, schema_fragment, fragment_data, previous_object_data,
            widget_factory, parent=parent
        )

    def build(self):
        groupBox = QtWidgets.QGroupBox(self.name.capitalize())
        layout = QtWidgets.QVBoxLayout()
        layout.setAlignment(QtCore.Qt.AlignTop)
        groupBox.setLayout(layout)
        groupBox.setFlat(False)
        groupBox.layout().setContentsMargins(0, 0, 0, 0)
        groupBox.setToolTip(self.description)

        self._accordion_widgets = []

        if 'items' in self.schema_fragment and self.fragment_data:
            for data in self.fragment_data:
                if type(data) == dict:
                    name = data.get('name')
                    self._type = data.get('type')
                else:
                    name = data
                optional_component = False
                for package in self.widget_factory.package['components']:
                    if package['name'] == name:
                        optional_component = data.get('optional', False)
                        break

                accordion_widget = AccordionWidget(
                    title=name, checkable=optional_component
                )
                obj = self.widget_factory.create_widget(
                    name, self.schema_fragment['items'], data,
                    self.previous_object_data
                )
                obj.layout().setContentsMargins(0, 0, 0, 0)
                obj.layout().setSpacing(0)
                accordion_widget.add_widget(obj)

                groupBox.layout().addWidget(accordion_widget)
                self._accordion_widgets.append(accordion_widget)
        self.layout().setContentsMargins(0, 0, 0, 0)

        self.layout().addWidget(groupBox)

    def to_json_object(self):
        out = []
        for accordion_widget in self._accordion_widgets:
            for idx in range(0, accordion_widget.count_widgets()):
                widget = accordion_widget.get_witget_at(idx)
                if 'to_json_object' in dir(widget):
                    data = widget.to_json_object()
                    data['enabled'] = accordion_widget.is_checked()
                    out.append(data)
        return out

class StepArrayContext(BaseJsonWidget):
    '''
    Override widget representation of an array
    '''

    def __init__(
            self, name, schema_fragment, fragment_data,
            previous_object_data, widget_factory, parent=None
    ):
        '''Initialise StepArray with *name*, *schema_fragment*,
        *fragment_data*, *previous_object_data*, *widget_factory*, *parent*'''
        super(StepArrayContext, self).__init__(
            name, schema_fragment, fragment_data, previous_object_data,
            widget_factory, parent=parent
        )

    def build(self):
        if 'items' in self.schema_fragment and self.fragment_data:
            for data in self.fragment_data:
                if type(data) == dict:
                    name = data.get('name')
                    self._type = data.get('type')
                else:
                    name = data
                widget = self.widget_factory.create_widget(
                    name, self.schema_fragment['items'], data,
                    self.previous_object_data
                )
                widget.layout().setContentsMargins(0, 0, 0, 0)
                widget.layout().setSpacing(0)
                self.layout().addWidget(widget)
        self.layout().setContentsMargins(0, 0, 0, 0)

    def to_json_object(self):
        out = []
        for i in range(0, self.layout().count()):
            widget = self.layout().itemAt(i).widget()
            if 'to_json_object' in dir(widget):
                out.append(widget.to_json_object())
        return out