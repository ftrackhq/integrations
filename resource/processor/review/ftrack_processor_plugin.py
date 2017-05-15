# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

import os
import tempfile
import threading

import nuke

import ftrack_api

import ftrack_connect_nuke_studio.processor

FILE_PATH = os.path.dirname(os.path.abspath(__file__))


def publish_reviewable_component(version_id, component, out):
    '''Publish a reviewable component to *version_id*'''

    session = ftrack_api.Session()

    version = session.get(
        'AssetVersion', version_id
    )

    version.create_component(
        out, data={'name':component}, location='auto'
    )

    session.commit()

    session.encode_media(
        out, version_id=version_id
    )



def create_review():
    ''' Create component callback for nuke write nodes.

    This callback relies on two custom knobs:
        * asset_version_id , which refers to the parent Asset.
        * component_name, the component which will contain the node result.

    This callback will also trigger the upload and encoding of the generated
    quicktime.

    '''

    node = nuke.thisNode()
    version_id = node['asset_version_id'].value()
    out = str(node['file'].value())
    component = node['component_name'].value()

    # Create component in a separate thread. If this is done in the main thread
    # the file is not properly written to disk.
    _thread = threading.Thread(
        target=publish_reviewable_component,
        kwargs={
            'version_id': version_id,
            'component': component,
            'out': out
        }
    )
    _thread.start()


class ReviewPlugin(ftrack_connect_nuke_studio.processor.ProcessorPlugin):
    '''Generate review media.'''

    def __init__(self, session, *args, **kwargs):
        '''Initialise processor.'''
        super(ReviewPlugin, self).__init__(
            *args, **kwargs
        )

        self.session = session

        self.name = 'processor.review'
        self.defaults = {
            'OUT': {
                'file_type': 'mov',
                'mov64_codec': 'jpeg',
                'afterRender': (
                    'import sys;'
                    'sys.path.append("{path}");'
                    'import ftrack_processor_plugin;'
                    'ftrack_processor_plugin.create_review()'
                ).format(path=self.escape_file_path(FILE_PATH))
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
        self.session.event_hub.subscribe(
            'topic=ftrack.processor.discover and '
            'data.object_type=shot',
            self.discover
        )
        self.session.event_hub.subscribe(
            'topic=ftrack.processor.launch and data.name={0}'.format(
                self.name
            ),
            self.launch
        )


def register(session, **kw):
    '''Register plugin. Called when used as an plugin.'''
    # Validate that session is an instance of ftrack_api.Session. If not,
    # assume that register is being called from an old or incompatible API and
    # return without doing anything.
    if not isinstance(session, ftrack_api.session.Session):
        return

    plugin = ReviewPlugin(
        session
    )

    plugin.register()

