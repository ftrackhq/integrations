# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack
import logging

from ftrack_connect_pipeline_qt.ui.client import BaseUIWidget
from ftrack_connect_pipeline_qt.ui.utility.widget.accordion import AccordionWidget
from ftrack_connect_pipeline_qt.ui.utility.widget.base.accordion_base import  AccordionBaseWidget

class PluginAccordion(AccordionBaseWidget):

    @property
    def options_widget(self):
        return self._options_button

    def __init__(self, title=None, checkable=False, parent=None):
        super(PluginAccordion,self).__init__(parent=parent, title=title, checkable=checkable)

    #def init_status_label(self):
    #    self._status_label = QtWidgets.QLabel()
    #    self._status_label.setObjectName('purple')
    #    return self._status_label

    #def init_options_button(self):
    #    self._options_button = OptionsButton('O', qta.icon('mdi6.cog',color='gray'))
    #    self._options_button.setObjectName('borderless')
    #    return self._options_button

    #def init_status_icon(self):
    #    self._status_icon = MaterialIconWidget('check')
    #    self._status_icon.setObjectName('borderless')
    #    return self._status_icon

    def init_header_content(self,layout, collapsed):
        '''Add publish related widgets to the accordion header'''
        #layout.addWidget(self.init_status_label())
        layout.addStretch()
        #layout.addWidget(line.Line(horizontal=True))
        #layout.addWidget(self.init_options_button())
        #layout.addWidget(line.Line(horizontal=True))
        #layout.addWidget(self.init_status_icon())

    def on_collapse(self, collapsed):
        '''Callback on accordion collapse/expand.'''
        pass

    def update_input(self, message, status):
        '''(Override)'''
        pass


class AccordionPluginContainerWidget(BaseUIWidget):
    '''Widget representation of a boolean'''
    def __init__(self, name, fragment_data, parent=None):
        '''Initialise JsonBoolean with *name*, *schema_fragment*,
        *fragment_data*, *previous_object_data*, *widget_factory*, *parent*'''
        super(AccordionPluginContainerWidget, self).__init__(
            name, fragment_data, parent=parent
        )

    def build(self):
        self._widget = PluginAccordion(
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