# :coding: utf-8
# :copyright: Copyright (c) 2014 ftrack

import os
import tempfile

import ftrack_connect_nuke_studio.processor


class PublishPlugin(ftrack_connect_nuke_studio.processor.ProcessorPlugin):
    '''Publish component data.'''

    def __init__(self):
        '''Initialise processor.'''
        super(PublishPlugin, self).__init__()
        self.name = 'processor.publish'
        self.defaults = {
            'OUT': {
                'file_type': 'dpx',
                'afterRender': (
                    'from ftrack_connect_nuke_studio.nuke_publish_cb '
                    'import createComponent;'
                    'createComponent()'
                )
            }
         }
        self.script = os.path.abspath(
            os.path.join(
                os.path.dirname(__file__), 'script.nk'
            )
        )

    def prepare_data(self, data):
        '''Return data mapping processed from input *data*.'''
        data = super(PublishPlugin, self).prepare_data(data)

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
    plugin_publish = PublishPlugin()
    registry.add(plugin_publish)
