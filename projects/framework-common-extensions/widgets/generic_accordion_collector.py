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
from ftrack_qt.widgets.browsers import FileBrowser


SUPPORTED_COLLECTORS = ['FileBrowser']


class GenericAccordionCollectorWidget(BaseWidget):
    '''Main class to represent a context widget on a publish process.'''

    name = 'generic_accordion_collector'
    ui_type = 'qt'

    path_changed = QtCore.Signal(object)

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

        self._on_add_component_callback(collector_widget_name='FileBrowser')

        self._circular_add_button = CircularButton('add', variant='outlined')
        self._menu_button = MenuButton(self._circular_add_button)
        for collector_widget in self.plugin_config.get('options', {}).get(
            'available_collector_widgets', 'FileBrowser'
        ):
            self._menu_button.add_item(
                item_data=collector_widget,
                label=collector_widget,
            )

        self.layout().addWidget(self._menu_button)

    def _on_add_component_callback(self, collector_widget_name):
        editable_component_name = self.plugin_config.get('options', {}).get(
            'editable_component_name', True
        )
        # TODO: initialize accordion without exporters button and without validators btton
        accordion_widget = AccordionBaseWidget(
            selectable=False,
            show_checkbox=False,
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
        if collector_widget_name not in SUPPORTED_COLLECTORS:
            self.logger.warning(
                f"Collector widget not supported: {collector_widget_name}"
            )
            QMessage_box = QtWidgets.QMessageBox()
            QMessage_box.setText(
                f"Collector widget not supported: {collector_widget_name}"
            )
            QMessage_box.exec_()
            return
        widget_cls = globals()[collector_widget_name]
        widget_instance = widget_cls()
        accordion_widget.add_widget(widget_instance)
        if hasattr(widget_instance, 'path_changed'):
            if editable_component_name:
                widget_instance.path_changed.connect(
                    partial(self._on_path_changed_callback, accordion_widget)
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
        return 0

    def _on_component_name_edited_callback(self, new_name):
        new_name = self.get_available_component_name(
            new_name, skip_widget=self.sender()
        )
        if self.sender().previous_title:
            options = self.plugin_options.get(self.sender().previous_title)
            self.remove_plugin_option(self.sender().previous_title)
            self.set_plugin_option(new_name, options)

        self.sender().set_title(new_name)

    def _on_component_removed_callback(self):
        self.remove_plugin_option(self.sender().title)
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
        self.remove_plugin_option(accordion_widget.title)
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
        self.set_plugin_option(accordion_widget.title, option_value)

        # self.path_changed.emit(file_path)

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
