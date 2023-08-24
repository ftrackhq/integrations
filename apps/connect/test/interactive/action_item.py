# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from Qt import QtGui, QtWidgets
import ftrack_api
from ftrack_connect.ui.widget.action_item import ActionItem
from ftrack_connect.ui.widget.flow_layout import ScrollingFlowWidget
from harness import Harness


ACTIONS = [
    [
        dict(
            label='Mega Modeling',
            variant='2014',
            description='Launch mega modeling description.',
            actionIdentifier='my-action-callback-identifier',
            icon='https://www.ftrack.com/wp-content/uploads/logo-75px-3.png',
            actionData=dict(applicationIdentifier='mega_modeling_2014'),
        )
    ],
    [
        dict(
            label='Professional Painter',
            icon='photoshop',
            variant='v1',
            actionIdentifier='my-action-callback-identifier',
            actionData=dict(applicationIdentifier='professional_painter'),
        ),
        dict(
            label='Professional Painter',
            icon='photoshop',
            variant='v2',
            actionIdentifier='my-action-callback-identifier',
            actionData=dict(applicationIdentifier='professional_painter'),
        ),
    ],
    [
        dict(
            label='Cool Compositor v2',
            actionIdentifier='my-action-callback-identifier',
            actionData=dict(
                cc_plugins=['foo', 'bar'], applicationIdentifier='cc_v2'
            ),
        )
    ],
]


class WidgetHarness(Harness):
    '''Test harness for widget.'''

    def constructWidget(self):
        '''Return widget instance to test.'''

        widget = ScrollingFlowWidget(self.session)
        for item in 10 * ACTIONS:
            widget.addWidget(ActionItem(self.session, item))

        return widget


if __name__ == '__main__':
    raise SystemExit(WidgetHarness().run())
