# :coding: utf-8
# :copyright: Copyright (c) 2017 ftrack

from ftrack_connect_pipeline.ui.publish import dialog


class Publish(object):
    '''Publish tool.'''

    def __init__(self, plugin):
        '''Initialise with *plugin*.'''
        self.plugin = plugin

    def open(self):
        '''Create and open the global context switch.'''
        publish_dialog = dialog.Dialog(
            self.plugin.get_context(), self.plugin.api_session
        )
        publish_dialog.setMinimumSize(800, 600)
        publish_dialog.exec_()
