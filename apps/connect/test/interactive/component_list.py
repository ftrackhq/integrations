# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import ftrack_connect.ui.widget.components_list
from harness import Harness


class WidgetHarness(Harness):
    '''Test harness for widget.'''

    def constructWidget(self):
        '''Return widget instance to test.'''
        widget = ftrack_connect.ui.widget.components_list.ComponentsList()
        widget.addItem({'resourceIdentifier': '/path/to/file.png'})
        widget.addItem(
            {'resourceIdentifier': '/path/to/sequence.%04d.png [1-20]'}
        )

        return widget


if __name__ == '__main__':
    raise SystemExit(WidgetHarness().run())
