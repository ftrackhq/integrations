# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

from ftrack_connect_pipeline_qt.ui.utility.widget.base.accordion_base import (
    AccordionBaseWidget,
)


class AccordionWidget(AccordionBaseWidget):
    '''Simple base implementation of an accordion'''

    def __init__(
        self,
        parent=None,
        title=None,
        checkable=False,
        checked=True,
        collapsed=False,
        collapsable=True,
    ):
        super(AccordionWidget, self).__init__(
            AccordionBaseWidget.SELECT_MODE_NONE,
            AccordionBaseWidget.CHECK_MODE_CHECKBOX
            if checkable
            else AccordionBaseWidget.CHECK_MODE_CHECKBOX_DISABLED,
            checked=checked,
            title=title,
            collapsed=collapsed,
            collapsable=collapsable,
            parent=parent,
        )
