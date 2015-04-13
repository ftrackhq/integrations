# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

import os
import tempfile
import threading

import ftrack
import nuke

import ftrack_connect_nuke_studio.processor

FILE_PATH = os.path.dirname(os.path.abspath(__file__))


def publishReviewableComponent(version_id, component, out):
    '''Publish a reviewable component to *version_id*'''
    version = ftrack.AssetVersion(id=version_id)
    version.createComponent(component, out)

    ftrack.Review.makeReviewable(version=version, filePath=out)


def createReview():
    ''' Create component callback for nuke write nodes.

    This callback relies on two custom knobs:
        * asset_version_id , which refers to the parent Asset.
        * component_name, the component which will contain the node result.

    This callback will also trigger the upload and encoding of the generated
    quicktime.

    '''
    ftrack.setup()
    node = nuke.thisNode()
    version_id = node['asset_version_id'].value()
    out = str(node['file'].value())
    component = node['component_name'].value()

    # Create component in a separate thread. If this is done in the main thread
    # the file is not properly written to disk.
    _thread = threading.Thread(
        target=publishReviewableComponent,
        kwargs={
            'version_id': version_id,
            'component': component,
            'out': out
        }
    )
    _thread.start()


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
                    'import sys;'
                    'sys.path.append("{path}");'
                    'import plugin;'
                    'plugin.createReview()'
                ).format(path=FILE_PATH)
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

    def discover(self, event):
        '''Return discover data for *event*.'''
        return {
            'defaults': self.defaults,
            'name': 'Review',
            'processor_name': self.name,
            'asset_name': 'BG'
        }

    def launch(self, event):
        '''Launch processor from *event*.'''
        input = event['data'].get('input', {})
        self.process(input)

    def register(self):
        '''Register processor'''
        ftrack.EVENT_HUB.subscribe(
            'topic=ftrack.processor.discover and '
            'data.object_type=shot',
            self.discover
        )
        ftrack.EVENT_HUB.subscribe(
            'topic=ftrack.processor.launch and data.name={0}'.format(
                self.name
            ),
            self.launch
        )


def register(registry, **kw):
    '''Register hooks thumbnail processor.'''
    plugin = ReviewPlugin()
    plugin.register()
