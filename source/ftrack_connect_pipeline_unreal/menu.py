# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

host = None


def launch_dialog(widget_name):
    '''Send an event to open *widget_name* client.'''
    host.launch_client(widget_name)
