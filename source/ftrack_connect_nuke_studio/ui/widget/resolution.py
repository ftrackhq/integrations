# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

import hiero


class Resolution(hiero.ui.FormatChooser):
    '''Wrap hiero widget for promoted qtDesigner one.'''

    def __init__(self, *args, **kwargs):
        '''Initialise format chooser.'''
        super(Resolution, self).__init__(*args, **kwargs)

        default_value = kwargs.get('default_value')
        if default_value:
            self.setCurrentFormat(default_value)
