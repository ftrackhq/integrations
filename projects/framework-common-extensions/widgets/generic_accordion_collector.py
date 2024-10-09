# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack
import os.path

try:
    from PySide6 import QtWidgets, QtCore
except ImportError:
    from PySide2 import QtWidgets, QtCore

from functools import partial
import clique

from ftrack_framework_qt.widgets import BaseWidget

from ftrack_qt.widgets.accordion import AccordionBaseWidget
from ftrack_qt.widgets.buttons import CircularButton
from ftrack_qt.widgets.buttons import MenuButton

# TODO: Remove this from qt widgets as it needs to be loaded from the registry
from ftrack_qt.widgets.browsers import FileBrowser

from ftrack_qt.utils.decorators import invoke_in_qt_main_thread


class GenericObjectCollectorWidget(QtWidgets.QWidget):
    '''Main class to represent a context widget on a publish process.'''

    items_changed = QtCore.Signal(object)
    collect_items = QtCore.Signal()

    def __init__(
        self,
        parent=None,
    ):
        '''initialise PublishContextWidget with *parent*, *session*, *data*,
        *name*, *description*, *options* and *context*
        '''
        super(GenericObjectCollectorWidget, self).__init__(parent)
        self._object_list = None
        self._add_button = None
        self._remove_button = None
        self.pre_build_ui()
        self.build_ui()
        self.post_build_ui()

    def pre_build_ui(self):
        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(QtCore.Qt.AlignTop)
        self.setLayout(layout)
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed
        )

    def build_ui(self):
        '''build function widgets.'''

        self._object_list = QtWidgets.QListWidget()

        buttons_layout = QtWidgets.QHBoxLayout()
        self._add_button = QtWidgets.QPushButton('Add')
        self._remove_button = QtWidgets.QPushButton('Remove')

        self.layout().addWidget(self._object_list)
        buttons_layout.addWidget(self._add_button)
        buttons_layout.addWidget(self._remove_button)
        self.layout().addLayout(buttons_layout)

    def post_build_ui(self):
        '''hook events'''
        self._add_button.clicked.connect(self._on_add_object_callback)
        self._remove_button.clicked.connect(self._on_remove_object_callback)

    def _on_add_object_callback(self):
        self.collect_items.emit()

    def _on_remove_object_callback(self):
        selected_items = self._object_list.selectedItems()
        for item in selected_items:
            self._object_list.takeItem(self._object_list.row(item))
        self.items_changed.emit(self._get_items())

    def _get_items(self):
        items = []
        for index in range(0, self._object_list.count()):
            items.append(self._object_list.item(index))
        return items

    def add_items(self, items):
        self._object_list.addItems(items)
        self.items_changed.emit(self._get_items())

    def remove_items(self, items, emit_signal=True):
        for item in items:
            self._object_list.takeItem(self._object_list.row(item))
        if emit_signal:
            self.items_changed.emit(self._get_items())


class GenericAccordionCollectorWidget(BaseWidget):
    '''Main class to represent a context widget on a publish process.'''

    name = 'generic_accordion_collector'
    ui_type = 'qt'

    path_changed = QtCore.Signal(object)

    def get_available_widgets(self):
        return [FileBrowser, GenericObjectCollectorWidget]

    def __init__(
        self,
        event_manager,
        client_id,
        context_id,
        plugin_config,
        group_config,
        on_set_plugin_option,
        on_run_ui_hook,
        parent=None,
    ):
        '''initialise PublishContextWidget with *parent*, *session*, *data*,
        *name*, *description*, *options* and *context*
        '''
        self._accordion_widgets_registry = []
        self._circular_add_button = None
        self._menu_button = None

        super(GenericAccordionCollectorWidget, self).__init__(
            event_manager,
            client_id,
            context_id,
            plugin_config,
            group_config,
            on_set_plugin_option,
            on_run_ui_hook,
            parent,
        )

    def pre_build_ui(self):
        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(QtCore.Qt.AlignTop)
        self.setLayout(layout)
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed
        )

    def build_ui(self):
        '''build function widgets.'''
        available_widgets = self.get_available_widgets()

        self._on_add_component_callback(
            collector_widget_class=available_widgets[0]
        )

        self._circular_add_button = CircularButton('add', variant='outlined')
        self._menu_button = MenuButton(self._circular_add_button)
        for collector_widget in available_widgets:
            self._menu_button.add_item(
                item_data=collector_widget,
                label=collector_widget.__name__,
            )

        self.layout().addWidget(self._menu_button)

    def _on_add_component_callback(self, collector_widget_class):
        editable_component_name = self.plugin_config.get('options', {}).get(
            'editable_component_name', True
        )
        # TODO: initialize accordion without exporters button and without validators btton
        accordion_widget = AccordionBaseWidget(
            selectable=False,
            show_checkbox=False,
            show_settings=False,
            show_status=False,
            checkable=False,
            title="<Set Component Name>",
            editable_title=editable_component_name,
            selected=False,
            checked=True,
            collapsable=True,
            collapsed=True,
            removable=True,
        )

        accordion_widget.title_edited.connect(
            self._on_component_name_edited_callback
        )
        accordion_widget.bin_clicked.connect(
            self._on_component_removed_callback
        )

        # TODO: Could be good to have the registry in the widgets as well,
        #  so we could query the available widgets in there.
        #  But for now we will hardcode it.
        if str(collector_widget_class) not in str(
            self.get_available_widgets()
        ):
            self.logger.warning(
                f"Collector widget not supported: {str(collector_widget_class)}"
            )
            QMessage_box = QtWidgets.QMessageBox()
            QMessage_box.setText(
                f"Collector widget not supported: {str(collector_widget_class)}"
            )
            QMessage_box.exec_()
            return
        widget_instance = collector_widget_class()
        accordion_widget.add_widget(widget_instance)
        if hasattr(widget_instance, 'path_changed'):
            if editable_component_name:
                widget_instance.path_changed.connect(
                    partial(self._on_path_changed_callback, accordion_widget)
                )
        if hasattr(widget_instance, 'items_changed'):
            widget_instance.items_changed.connect(
                partial(self._on_items_changed_callback, accordion_widget)
            )
        if hasattr(widget_instance, 'collect_items'):
            widget_instance.collect_items.connect(
                self._on_collect_items_callback
            )
        self._accordion_widgets_registry.append(accordion_widget)
        latest_idx = self._get_latest_component_index()
        self.layout().insertWidget(latest_idx + 1, accordion_widget)

    def post_build_ui(self):
        '''hook events'''
        self._menu_button.item_clicked.connect(self._on_add_component_callback)

    def _get_latest_component_index(self, idx=1):
        # Get the number of items in the layout
        count = self.layout().count()
        if count > 0:
            # Get the last item
            item = self.layout().itemAt(count - idx)
            if item:
                if item.widget() in self._accordion_widgets_registry:
                    # Return the widget associated with the item
                    return self.layout().indexOf(item.widget())
                else:
                    return self._get_latest_component_index(idx + 1)
        return -1

    def _on_component_name_edited_callback(self, new_name):
        new_name = self.get_available_component_name(
            new_name, skip_widget=self.sender()
        )
        if self.sender().previous_title:
            current_components = self.plugin_options.get('components', {})
            component_options = current_components.get(
                self.sender().previous_title
            )
            if current_components.get(self.sender().previous_title):
                current_components.pop(self.sender().previous_title)
                current_components.update({new_name: component_options})
            self.set_plugin_option('components', current_components)

        self.sender().set_title(new_name)

    def _on_component_removed_callback(self):
        current_components = self.plugin_options.get('components', {})
        current_components.pop(self.sender().title)
        # Remove the widget from the registry
        self._accordion_widgets_registry.remove(self.sender())
        # Remove the widget from the layout
        self.sender().teardown()
        self.sender().deleteLater()

    def _on_path_changed_callback(self, accordion_widget, file_path):
        '''
        Callback to update the component name when the path is changed.
        Updates the option dictionary with provided *asset_name* when
        asset_changed of asset_selector event is triggered
        '''
        current_components = self.plugin_options.get('components', {})
        if current_components.get(accordion_widget.title):
            current_components.pop(accordion_widget.title)
        if not file_path:
            return

        file_extension = None
        try:
            collection = clique.parse(file_path)
            if collection:
                file_extension = collection.tail
        except Exception as error:
            self.logger.debug(
                f"{file_path} is not a clique collection. Error {error}"
            )

        if not file_extension:
            file_extension = os.path.splitext(file_path)[
                1
            ] or os.path.basename(file_path)

        file_extension = file_extension.lstrip('.')

        extension = self.get_available_component_name(file_extension)

        accordion_widget.set_title(extension)

        option_value = {
            'file_path': file_path,
        }

        current_components.update({accordion_widget.title: option_value})
        self.set_plugin_option('components', current_components)

        # self.path_changed.emit(file_path)

    def _on_items_changed_callback(self, accordion_widget, items_list):
        '''
        Callback to update the component name when the path is changed.
        Updates the option dictionary with provided *asset_name* when
        asset_changed of asset_selector event is triggered
        '''
        current_components = self.plugin_options.get('components', {})
        if current_components.get(accordion_widget.title):
            current_components.pop(accordion_widget.title)
        if not items_list:
            return

        component_name = accordion_widget.title
        if not component_name or component_name == '<Set Component Name>':
            self.logger.warning(
                f"No component name has been set. Please set a component name before continue."
            )
            QMessage_box = QtWidgets.QMessageBox()
            QMessage_box.setText(
                f"Please set a component name before collecting objects"
            )
            QMessage_box.exec_()
            self.sender().remove_items(items_list, emit_signal=False)
            return

        option_value = {
            'items_list': [item.text() for item in items_list],
        }

        current_components.update({accordion_widget.title: option_value})
        self.set_plugin_option('components', current_components)

    def _on_collect_items_callback(self):
        payload = {'widget': self.sender()}
        self.run_ui_hook(payload)

    @invoke_in_qt_main_thread
    def ui_hook_callback(self, ui_hook_result):
        '''Handle the result of the UI hook.'''
        super(GenericAccordionCollectorWidget, self).ui_hook_callback(
            ui_hook_result
        )
        ui_hook_result.get("widget").add_items(ui_hook_result.get("items"))

    def get_available_component_name(self, name, skip_widget=None):
        def increment_name(name):
            if '_' in name and name.rsplit('_', 1)[-1].isdigit():
                base, num = name.rsplit('_', 1)
                return f'{base}_{int(num) + 1}'
            else:
                return f'{name}_1'

        for widget in self._accordion_widgets_registry:
            if widget != skip_widget:
                if widget.title == name:
                    return self.get_available_component_name(
                        increment_name(name), skip_widget
                    )
        return name
