# :coding: utf-8
# :copyright: Copyright (c) 2014 ftrack

import os
import tempfile

import ftrack_connect_nuke_studio.processor


class ProxyPlugin(ftrack_connect_nuke_studio.processor.ProcessorPlugin):
    '''Generate proxies.'''

    def __init__(self):
        '''Initialise processor.'''
        super(ProxyPlugin, self).__init__()
        self.name = 'processor.proxy'
        self.defaults = {
            'OUT': {
                'file_type': 'png',
                'afterRender': (
                    'from ftrack_connect_nuke_studio.nuke_publish_cb '
                    'import createComponent;'
                    'createComponent()'
                )
            },
            'REFORMAT': {
                'type': 'to box',
                'scale': 0.5
            }
        }
        self.script = os.path.abspath(
            os.path.join(
                os.path.dirname(__file__), 'script.nk'
            )
        )

    def prepare_data(self, data):
        '''Return data mapping processed from input *data*.'''
        data = super(ProxyPlugin, self).prepare_data(data)

        # Define output file sequence.
        format = '.####.{0}'.format(data['OUT']['file_type'])
        name = self.name.replace('.', '_')
        temporary_path = tempfile.NamedTemporaryFile(
            prefix=name, suffix=format, delete=False
        )
        data['OUT']['file'] = temporary_path.name.replace('\\', '/')

        return data


def register(registry):
    '''Register plugin with *registry*.'''
    plugin_proxy = ProxyPlugin()
    registry.add(plugin_proxy)
