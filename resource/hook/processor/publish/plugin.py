# :coding: utf-8
# :copyright: Copyright (c) 2014 ftrack

import os
import tempfile

import ftrack
import nuke
from clique import Collection

import ftrack_connect_nuke_studio.processor

FILE_PATH = os.path.abspath(__file__)


def createComponent():
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

    # Create the component and copy data to the most likely store
    component = node['component_name'].value()
    out = node['file'].value()

    prefix = out.split('.')[0] + '.'
    ext = os.path.splitext(out)[-1]
    start_frame = int(node['first'].value())
    end_frame = int(node['last'].value())
    collection = Collection(
        head=prefix,
        tail=ext,
        padding=len(str(end_frame)),
        indexes=set(range(start_frame, end_frame + 1))
    )
    component = version.createComponent(component, str(collection))
    component.setMeta('img_main', True)


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
                    'import imp;'
                    'processor = imp.load_source("{module}", "{path}");'
                    'processor.createComponent()'
                ).format(module='plugin', path=FILE_PATH)
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
        return {
            'defaults': self.defaults,
            'name': 'Ingest',
            'processor_name': self.name,
            'asset_name': 'BG'
        }

    def launch(self, event):
        input = event['data'].get('input', {})
        self.process(input)

    def register(self, classifier):
        ftrack.EVENT_HUB.subscribe(
            'topic=ftrack.processor.discover and {0}'.format(classifier),
            self.discover
        )
        ftrack.EVENT_HUB.subscribe(
            'topic=ftrack.processor.launch and data.name={0}'.format(
                self.name
            ),
            self.launch
        )


def register(registry, **kw):
    '''Register hooks for ftrack connect legacy plugins.'''
    proxyPlugin = PublishPlugin()
    proxyPlugin.register('data.name=Animation and data.object_type=task')
