# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack
import logging

from Qt import QtWidgets

from ftrack_connect_pipeline_qt.ui.factory.base import BaseUIWidgetObject
from ftrack_connect_pipeline_qt.ui.utility.widget.base.accordion_base import (
    AccordionBaseWidget,
)


class PluginAccordion(AccordionBaseWidget):
    '''Accordion widget representation of a schema plugin'''

    @property
    def options_widget(self):
        '''Return the options widget'''
        return self._options_button

    def __init__(self, title=None, checkable=False, checked=True, parent=None):
        '''
        Initialize the plugin accordion

        :param title: The name of the plugin
        :param checkable: True if user can check and uncheck it or not
        :param checked: True if the plugin is checked by default
        :param parent: the parent dialog or frame
        '''
        super(PluginAccordion, self).__init__(
            AccordionBaseWidget.SELECT_MODE_NONE,
            AccordionBaseWidget.CHECK_MODE_CHECKBOX
            if checkable
            else AccordionBaseWidget.CHECK_MODE_CHECKBOX_DISABLED,
            checked=checked,
            title=title,
            parent=parent,
        )

    def init_header_content(self, header_widget, collapsed):
        '''(Override) Setup the header widget layout'''
        header_layout = QtWidgets.QHBoxLayout()
        header_widget.setLayout(header_layout)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(0)
        header_layout.addStretch()

    def on_collapse(self, collapsed):
        '''Callback on accordion collapse/expand.'''
        pass


class AccordionPluginContainerWidgetObject(BaseUIWidgetObject):
    '''Widget representation of an accordion plugin container'''

    def __init__(self, name, fragment_data, parent=None):
        '''Initialise AccordionPluginContainerWidgetObject with *name*,
        *fragment_data* and *parent*'''
        super(AccordionPluginContainerWidgetObject, self).__init__(
            name, fragment_data, parent=parent
        )

    def build(self):
        '''(Override) Build the widget'''
        self._widget = PluginAccordion(
            title=self.name, checkable=self.optional, checked=self.enabled
        )

    def parent_widget(self, widget, add_line=False):
        '''(Override)'''
        if self.widget:
            widget = (
                widget.widget
                if isinstance(widget, BaseUIWidgetObject)
                else widget
            )
            self.widget.add_widget(widget)
        else:
            self.logger.error("Please create a widget before parent")
