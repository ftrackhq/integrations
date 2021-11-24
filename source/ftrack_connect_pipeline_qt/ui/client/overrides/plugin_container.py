# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

import logging
from ftrack_connect_pipeline_qt.ui.client import BaseUIWidget
from ftrack_connect_pipeline_qt.ui.utility.widget.accordion import AccordionWidget


class AccordionPluginContainerWidget(BaseUIWidget):
    '''Widget representation of a boolean'''
    def __init__(self, name, fragment_data, parent=None):
        '''Initialise JsonBoolean with *name*, *schema_fragment*,
        *fragment_data*, *previous_object_data*, *widget_factory*, *parent*'''
        super(AccordionPluginContainerWidget, self).__init__(
            name, fragment_data, parent=parent
        )

    def build(self):
        self._widget = AccordionWidget(
            title=self.name, checkable=False
        )

    def parent_widget(self, widget):
        if self.widget:
            if isinstance(widget, BaseUIWidget):
                self.widget.add_widget(widget.widget)
            else:
                self.widget.add_widget(widget)
        else:
            self.logger.error("Please create a widget before parent")