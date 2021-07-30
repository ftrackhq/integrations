# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

import logging
from ftrack_connect_pipeline_qt.client.widgets.experimental.default.step_container import DefaultStepContainerWidget
from Qt import QtGui, QtCore, QtWidgets


class TabStepContainerWidget(DefaultStepContainerWidget):
    '''Widget representation of a boolean'''
    def __init__(self, name, fragment_data, parent=None):
        '''Initialise JsonBoolean with *name*, *schema_fragment*,
        *fragment_data*, *previous_object_data*, *widget_factory*, *parent*'''
        super(TabStepContainerWidget, self).__init__(
            name, fragment_data, parent=parent
        )

    def build(self):
        super(TabStepContainerWidget, self).build()
        self.tab_widget = QtWidgets.QTabWidget()
        self.widget.layout().addWidget(self.tab_widget)

    def parent_widget(self, step_widget):
        if self.tab_widget:
            if hasattr(step_widget, 'widget'):
                self.tab_widget.addTab(step_widget.widget, step_widget.name)
            else:
                self.tab_widget.addTab(step_widget, step_widget.name)
        else:
            self.logger.error("Please create a widget before parent")
