# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from ftrack_qt.widgets.accordion import AccordionWidget

from ftrack_qt.widgets.headers import (
    PublisherAccordionHeaderWidget,
)


class PublisherAccordionWidget(AccordionWidget):
    '''Accordion widget tailored for a publisher step'''

    def build_header(self):
        '''(Override) Provide an extended header with options and status icon'''
        return PublisherAccordionHeaderWidget(
            title=self.title,
            checkable=self.checkable,
            checked=self.checked,
            show_checkbox=self.show_checkbox,
            collapsable=self.collapsable,
            collapsed=self.collapsed,
        )

    def add_option_widget(self, widget, section_name):
        self._header_widget.add_option_widget(widget, section_name)
