# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

import os
import tempfile

import ftrack
import nuke
from clique import Collection

import ftrack_connect_nuke_studio.processor

FILE_PATH = os.path.dirname(os.path.abspath(__file__))


def _getSize(path):
    '''Return size from *path*'''
    try:
        size = os.path.getsize(path)
    except OSError:
        size = 0
    return size


def updateComponent():
    ''' Create component callback for nuke write nodes.

    This callback relies on two custom knobs:
        * asset_version_id , which refers to the parent Asset.
        * component_name, the component which will contain the node result.

    '''
    ftrack.setup()

    # Get the current node.
    node = nuke.thisNode()

    asset_id = node['asset_version_id'].value()
    version = ftrack.AssetVersion(id=asset_id)

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

    origin = ftrack.LOCATION_PLUGINS.get('ftrack.origin')

    # Get container component and update resource identifier.
    container = version.getComponent(node['component_name'].value())

    # Create member components.
    containerSize = 0
    for item in collection:
        size = _getSize(item)
        containerSize += size
        ftrack.createComponent(
            name=collection.match(item).group('index'),
            path=item,
            systemType='file',
            location=None,
            size=size,
            containerId=container.getId(),
            padding=None  # Padding not relevant for 'file' type.
        )

    container.set({
        'size': containerSize,
        'padding': padding,
        'filetype': ext
    })

    container.setResourceIdentifier(collection.format('{head}{padding}{tail}'))
    container = origin.addComponent(container, recursive=False)

    location = ftrack.pickLocation()
    location.addComponent(container)


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
                    'import sys;'
                    'sys.path.append("{path}");'
                    'import ftrack_processor_plugin;'
                    'ftrack_processor_plugin.updateComponent()'
                ).format(path=FILE_PATH)
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

    def process(self, data):
        '''Process *data* and assetise related track item.'''

        # The component has to be created before the render job is kicked off
        # in order to assetise the track_item.
        component = ftrack.createComponent(
            name=data['component_name'],
            versionId=data['asset_version_id'],
            systemType='sequence'
        )
        component.setMeta('img_main', True)

        track_item = data['application_object']
        track_item.source().setEntityReference(
            component.getEntityRef()
        )
        super(PublishPlugin, self).process(data)


def register(registry, **kw):
    '''Register hooks thumbnail processor.'''
    plugin = PublishPlugin()
    plugin.register()
