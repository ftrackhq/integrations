# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

import os
import tempfile
import logging

import nuke
from clique import Collection

import ftrack_connect_nuke_studio.processor
import ftrack_connect_nuke_studio.entity_reference


FILE_PATH = os.path.dirname(os.path.abspath(__file__))


def update_component():
    '''Update component callback for nuke write nodes.

    This callback relies on two custom knobs:
        * asset_version_id , which refers to the parent Asset.
        * component_name, the component which will contain the node result.

    '''

    # Import inline to avoid issue where platform.system() is called in
    # requests __init__.py.
    import ftrack_api

    session = ftrack_api.Session()

    # Get the current node.
    node = nuke.thisNode()

    asset_id = node['asset_version_id'].value()
    asset_version = session.get('AssetVersion', asset_id)

    out = node['file'].value()

    prefix = out.split('.')[0] + '.'
    ext = os.path.splitext(out)[-1]
    start_frame = int(node['first'].value())
    end_frame = int(node['last'].value())
    padding = len(str(end_frame))
    collection = Collection(
        head=prefix,
        tail=ext,
        padding=padding,
        indexes=set(range(start_frame, end_frame + 1))
    )

    container = session.query(
        u'Component where name = {0} and version_id= {1}'.format(
            node['component_name'].value(), node['asset_version_id'].value()
        )
    ).one()

    # Create member components.
    container_size = 0
    for item in collection:
        size = os.path.getsize(item)
        container_size += size

        session.create_component(
            item, data={
                'name': collection.match(item).group('index'),
                'system_type': 'file',
                'size': size,
                'container': container
            }, location=None
        )

    container.update({
        'size': container_size,
        'padding': padding,
        'file_type': ext
    })

    origin_location = session.get(
        'Location', ftrack_api.symbol.ORIGIN_LOCATION_ID
    )

    location = session.pick_location()

    location.add_component(container, origin_location)


class PublishPlugin(ftrack_connect_nuke_studio.processor.ProcessorPlugin):
    '''Publish component data.'''

    def __init__(self, session, *args, **kwargs):
        '''Initialise processor.'''
        super(PublishPlugin, self).__init__(
            *args, **kwargs
        )

        self.session = session

        self.name = 'processor.publish'
        self.defaults = {
            'OUT': {
                'file_type': 'dpx',
                'afterRender': (
                    'import sys;'
                    'sys.path.append("{path}");'
                    'import ftrack_processor_plugin;'
                    'ftrack_processor_plugin.update_component()'
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
        data = super(PublishPlugin, self).prepare_data(data)

        # Define output file sequence.
        format = '.####.{0}'.format(data['OUT']['file_type'])
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
            'name': 'Ingest',
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

    def process(self, data):
        '''Process *data* and assetise related track item.'''

        # The component has to be created before the render job is kicked off
        # in order to assetise the track_item. This is required since the render
        # job is asynchronous and might be offloaded to another machine in
        # future versions.

        component = self.session.create(
            'SequenceComponent', {
                'name': data['component_name'],
                'version_id': data['asset_version_id']
            }
        )

        component['metadata']['img_main'] = True

        track_item = data['application_object']

        self.session.commit()

        ftrack_connect_nuke_studio.entity_reference.set(
            track_item, component
        )

        super(PublishPlugin, self).process(data)


def register(session, **kw):

    logger = logging.getLogger(
        'ftrack_processor_plugin:publish.register'
    )

    # Import inline to avoid issue where platform.system() is called in
    # requests __init__.py.
    import ftrack_api

    '''Register plugin. Called when used as an plugin.'''
    # Validate that session is an instance of ftrack_api.Session. If not,
    # assume that register is being called from an old or incompatible API and
    # return without doing anything.
    if not isinstance(session, ftrack_api.session.Session):
        return


    plugin = PublishPlugin(
        session
    )

    plugin.register()

