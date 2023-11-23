# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import logging

import ftrack_connect.ui.widget.data_drop_zone
from harness import Harness


class WidgetHarness(Harness):
    '''Test harness for widget.'''

    def constructWidget(self):
        '''Return widget instance to test.'''
        widget = ftrack_connect.ui.widget.data_drop_zone.DataDropZone()
        widget.dataSelected.connect(logging.debug)
        return widget


if __name__ == '__main__':
    raise SystemExit(WidgetHarness().run())
