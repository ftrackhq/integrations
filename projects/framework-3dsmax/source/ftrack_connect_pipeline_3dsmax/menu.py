# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

host = None


class LaunchDialog(object):
    def __init__(self):
        super(LaunchDialog, self).__init__()

    def launch_dialog(self, widget_name):
        '''Send an event to open *widget_name* client.'''
        host.launch_client(widget_name)
