# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import ftrack_connect.ui.widget.thumbnail_drop_zone
from harness import Harness


class WidgetHarness(Harness):
    '''Test harness for widget.'''

    def constructWidget(self):
        '''Return widget instance to test.'''
        return ftrack_connect.ui.widget.thumbnail_drop_zone.ThumbnailDropZone()


if __name__ == '__main__':
    raise SystemExit(WidgetHarness().run())
