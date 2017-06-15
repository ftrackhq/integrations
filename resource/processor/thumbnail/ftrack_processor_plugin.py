# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

import os
import tempfile

import nuke

import ftrack_connect_nuke_studio.processor

FILE_PATH = os.path.dirname(os.path.abspath(__file__))


def create_thumbnail():
    ''' Create component callback for nuke write nodes.

    This callback relies on two custom knobs:
        * asset_version_id , which refers to the parent Asset.
        * component_name, the component which will contain the node result.

    This callback will also trigger upload of the thumbnail on the server.

    '''

    node = nuke.thisNode()
    out_file = node['file'].value()

    # Import inline to avoid issue where platform.system() is called in
    # requests __init__.py.
    import ftrack_api

    session = ftrack_api.Session()

    asset_version = session.get(
        'AssetVersion', node['asset_version_id'].value()
    )

    for entity in (asset_version,
                   asset_version.get('task'),
                   asset_version.get('asset').get('parent')):

        if entity is None:
            continue

        entity.create_thumbnail(
            out_file
        )

    if not os.environ.get(
        'FTRACK_CONNECT_NUKE_STUDIO_STOP_THUMBNAIL_PROPAGATION', False
    ):
        parent_entity = asset_version.get('asset').get('parent')

        for task in parent_entity.get('children'):
            task.create_thumbnail(
                out_file
            )

    session.commit()

class ThumbnailPlugin(ftrack_connect_nuke_studio.processor.ProcessorPlugin):
    '''Generate thumbnails.'''

    def __init__(self, session, *args, **kwargs):
        '''Initialise processor.'''
        super(ThumbnailPlugin, self).__init__(
            *args, **kwargs
        )

        self.session = session

        self.name = 'processor.thumbnail'
        self.chosen_frame = 1001
        self.defaults = {
            'OUT': {
                'file_type': 'jpeg',
                'first': self.chosen_frame,
                'last': self.chosen_frame,
                'afterRender': (
                    'import sys;'
                    'sys.path.append("{path}");'
                    'import ftrack_processor_plugin;'
                    'ftrack_processor_plugin.create_thumbnail()'
                ).format(path=self.escape_file_path(FILE_PATH))
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

    def discover(self, event):
        '''Return discover data for *event*.'''
        return {
            'defaults': self.defaults,
            'name': 'Thumbnail',
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
    # Import inline to avoid issue where platform.system() is called in
    # requests __init__.py.
    import ftrack_api

    # Validate that session is an instance of ftrack_api.Session. If not,
    # assume that register is being called from an old or incompatible API and
    # return without doing anything.
    if not isinstance(session, ftrack_api.session.Session):
        return

    plugin = ThumbnailPlugin(
        session
    )

    plugin.register()

