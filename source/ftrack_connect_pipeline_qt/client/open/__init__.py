#! /usr/bin/env python
# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack
import os

from Qt import QtWidgets, QtCore

from ftrack_connect_pipeline_qt import constants
from ftrack_connect_pipeline_qt import client
from ftrack_connect_pipeline_qt import constants as qt_constants
from ftrack_connect_pipeline_qt.client import factory
from ftrack_connect_pipeline_qt.ui.utility.widget import (
    dialog,
    definition_selector,
)
from ftrack_connect_pipeline_qt.ui.utility.widget.context_selector import (
    ContextSelector,
)


class QtOpenerClient(client.QtClient, dialog.Dialog):
    '''
    Base open widget class.
    '''

    definition_filter = 'opener'

    def __init__(
        self, event_manager, definition_extensions_filter=None, parent=None
    ):
        if not definition_extensions_filter is None:
            self.definition_extensions_filter = definition_extensions_filter

        dialog.Dialog.__init__(self, parent=parent)
        client.QtClient.__init__(self, event_manager)

        self.logger.debug('start qt opener')

        self.setWindowTitle('ftrack Open')
        self.resize(450, 530)

    def get_factory(self):
        return factory.OpenerWidgetFactory(
            self.event_manager,
            self.ui_types,
            parent=self.parent(),
        )

    def getThemeBackgroundStyle(self):
        return 'ftrack'

    def is_docked(self):
        return False

    def _build_context_selector(self):
        '''Instantiate a master context selector'''
        return ContextSelector(self.session, master=True, parent=self.parent())

    def _build_definition_selector(self):
        return definition_selector.OpenerDefinitionSelector(
            parent=self.parent()
        )

    def _build_button_widget(self):
        button_widget = QtWidgets.QWidget()
        button_widget.setLayout(QtWidgets.QHBoxLayout())
        button_widget.layout().setContentsMargins(10, 10, 10, 5)
        button_widget.layout().setSpacing(10)

        self.open_assembler_button = OpenAssemblerButton()
        button_widget.layout().addWidget(self.open_assembler_button)

        self.l_filler = QtWidgets.QLabel()
        button_widget.layout().addWidget(self.l_filler, 10)

        self.run_button = client.RunButton('OPEN')
        button_widget.layout().addWidget(self.run_button)
        self.run_button.setEnabled(False)
        return button_widget

    def post_build(self):
        super(QtOpenerClient, self).post_build()

        self.widget_factory.widgetAssetUpdated.connect(
            self._on_widget_asset_updated
        )

        self.widget_factory.widgetRunPlugin.connect(self._on_run_plugin)
        self.widget_factory.componentsChecked.connect(
            self._on_components_checked
        )
        self.open_assembler_button.clicked.connect(self._open_assembler)

    def _on_context_selector_context_changed(self, context):
        '''(Override) Context has been set in context selector'''
        if self.host_connection:
            # Send event to other listening clients
            self.host_connection.set_global_context(context)
        super(QtOpenerClient, self)._on_context_selector_context_changed(
            context
        )

    def change_definition(self, schema, definition, component_names_filter):
        super(QtOpenerClient, self).change_definition(
            schema, definition, component_names_filter
        )

    def definition_changed(self, definition, available_components_count):
        '''React upon change of definition, or no versions/components(definitions) available.'''
        if definition is not None and available_components_count >= 1:
            self.run_button.setEnabled(True)
        else:
            self.run_button.setEnabled(False)
            self._clear_widget()

    def run(self):
        if super(QtOpenerClient, self).run():
            self.widget_factory.progress_widget.set_status(
                constants.SUCCESS_STATUS, 'Successfully opened version!'
            )

    def reset(self):
        '''Open dialog is shown again after being hidden.'''
        self.host_and_definition_selector.refresh()

    def show(self):
        if self._shown:
            # Widget has been shown before, reset client
            self.reset()
        super(QtOpenerClient, self).show()
        self._shown = True


class OpenAssemblerButton(QtWidgets.QPushButton):
    def __init__(self, parent=None):
        super(OpenAssemblerButton, self).__init__(
            'OPEN ASSEMBLER', parent=parent
        )
