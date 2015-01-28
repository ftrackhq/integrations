# :coding: utf-8
# :copyright: Copyright (c) 2014 ftrack

import os
import tempfile

import ftrack_connect_nuke_studio.processor


class ReviewPlugin(ftrack_connect_nuke_studio.processor.ProcessorPlugin):
    '''Generate review media.'''

    def __init__(self):
        '''Initialise processor.'''
        super(ReviewPlugin, self).__init__()
        self.name = 'processor.review'
        self.defaults = {
            'OUT': {
                'file_type': 'mov',
                'mov64_codec': 'jpeg',
                'afterRender': (
                    'from ftrack_connect_nuke_studio.nuke_publish_cb '
                    'import createReview;'
                    'createReview()'
                )
            }
        }
        self.script = os.path.abspath(
            os.path.join(
                os.path.dirname(__file__), 'script.nk'
            )
        )
        self.format = '.mov'

    def prepare_data(self, data):
        '''Return data mapping processed from input *data*.'''
        data = super(ReviewPlugin, self).prepare_data(data)

        # Define output file.
        name = self.name.replace('.', '_')
        temporary_path = tempfile.NamedTemporaryFile(
            prefix=name, suffix=self.format, delete=False
        )
        data['OUT']['file'] = temporary_path.name.replace('\\', '/')

        return data


def register(registry):
    '''Register plugin with *registry*.'''
    plugin_review = ReviewPlugin()
    registry.add(plugin_review)
