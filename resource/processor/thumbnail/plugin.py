# :coding: utf-8
# :copyright: Copyright (c) 2014 ftrack

import os
import tempfile

import ftrack_connect_nuke_studio.processor


class ThumbnailPlugin(ftrack_connect_nuke_studio.processor.ProcessorPlugin):
    '''Generate thumbnails.'''

    def __init__(self):
        '''Initialise processor.'''
        super(ThumbnailPlugin, self).__init__()
        self.name = 'processor.thumbnail'
        self.chosen_frame = 1001
        self.defaults = {
            'OUT': {
                'file_type': 'jpeg',
                'first': self.chosen_frame,
                'last': self.chosen_frame,
                'afterRender': (
                    'from ftrack_connect_nuke_studio.nuke_publish_cb '
                    'import createThumbnail;'
                    'createThumbnail()'
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
        data = super(ThumbnailPlugin, self).prepare_data(data)

        # Define output file sequence.
        format = '.{0}.{1}'.format(self.chosen_frame, data['OUT']['file_type'])
        name = self.name.replace('.', '_')
        temporary_path = tempfile.NamedTemporaryFile(
            prefix=name, suffix=format, delete=False
        )
        data['OUT']['file'] = temporary_path.name.replace('\\', '/')

        return data


def register(registry):
    '''Register plugin with *registry*.'''
    plugin_thumbnail = ThumbnailPlugin()
    registry.add(plugin_thumbnail)
