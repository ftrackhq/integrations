# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

import os
import tempfile
import logging

import ftrack
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
    ftrack.setup()
    node = nuke.thisNode()

    asset_id = node['asset_version_id'].value()
    version = ftrack.AssetVersion(id=asset_id)
    out = node['file'].value()
    version.createThumbnail(out)

    shot = version.getAsset().getParent()
    shot.createThumbnail(out)

    if version.get('taskid'):
        task = version.getTask()
        task.createThumbnail(out)


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
                    'import sys;'
                    'sys.path.append("{path}");'
                    'import ftrack_processor_plugin;'
                    'ftrack_processor_plugin.create_thumbnail()'
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

    logger = logging.getLogger(
        'ftrack_processor_plugin:thumbnail.register'
    )

    # Validate that registry is an instance of ftrack.Registry. If not,
    # assume that register is being called from a new or incompatible API and
    # return without doing anything.
    if not isinstance(registry, ftrack.Registry):
        logger.debug(
            'Not subscribing plugin as passed argument {0!r} is not an '
            'ftrack.Registry instance.'.format(registry)
        )
        return

    plugin = ThumbnailPlugin()
    plugin.register()
