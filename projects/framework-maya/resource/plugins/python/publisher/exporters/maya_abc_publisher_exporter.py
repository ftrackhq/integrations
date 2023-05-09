# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

import tempfile

import maya.cmds as cmds

from ftrack_connect_pipeline_maya import plugin
import ftrack_api


class MayaAbcPublisherExporterPlugin(plugin.MayaPublisherExporterPlugin):
    '''Maya Alembic exporter plugin'''

    plugin_name = 'maya_abc_publisher_exporter'

    def fetch(self, context_data=None, data=None, options=None):
        '''Fetch start and end frames from the scene'''
        frame_info = {
            "frameStart": cmds.playbackOptions(q=True, ast=True),
            "frameEnd": cmds.playbackOptions(q=True, aet=True),
        }
        return frame_info

    def extract_options(self, options):

        return {
            'alembicAnimation': bool(options.get('alembicAnimation', True)),
            'frameStart': float(
                options.get(
                    'frameStart', cmds.playbackOptions(q=True, ast=True)
                )
            ),
            'frameEnd': float(
                options.get('frameEnd', cmds.playbackOptions(q=True, aet=True))
            ),
            'alembicUvwrite': bool(options.get('alembicUvwrite', True)),
            'alembicWorldspace': bool(options.get('alembicWorldspace', False)),
            'alembicWritevisibility': bool(
                options.get('alembicWritevisibility', False)
            ),
            'alembicEval': float(options.get('alembicEval', 1.0)),
        }

    def run(self, context_data=None, data=None, options=None):
        '''Export Maya alembic geometry based on collected objects in *data* and *options* supplied'''

        # ensure to load the alembic plugin
        cmds.loadPlugin('AbcExport.so', qt=1)

        new_file_path = tempfile.NamedTemporaryFile(
            delete=False, suffix='.abc'
        ).name

        options = self.extract_options(options)

        self.logger.debug(
            'Calling exporters options: data {}. options {}'.format(
                data, options
            )
        )

        collected_objects = []
        for collector in data:
            collected_objects.extend(collector['result'])

        cmds.select(cl=True)
        cmds.select(collected_objects)
        selectednodes = cmds.ls(sl=True, long=True)
        nodes = cmds.ls(selectednodes, type='transform', long=True)

        objCommand = ''
        for n in nodes:
            objCommand = objCommand + '-root ' + n + ' '

        alembicJobArgs = []

        if context_data['asset_type_name'] == 'cam':
            alembicJobArgs.append('-dataFormat ogawa')
        else:
            alembicJobArgs.append('-sl')

        if options.get('alembicUvwrite'):
            alembicJobArgs.append('-uvWrite')

        if options.get('alembicWorldspace'):
            alembicJobArgs.append('-worldSpace')

        if options.get('alembicWritevisibility'):
            alembicJobArgs.append('-writeVisibility')

        if options.get('alembicAnimation'):
            alembicJobArgs.append(
                '-frameRange {0} {1} -step {2} '.format(
                    options['frameStart'],
                    options['frameEnd'],
                    options['alembicEval'],
                )
            )

        alembicJobArgs = ' '.join(alembicJobArgs)
        alembicJobArgs += ' ' + objCommand + '-file ' + new_file_path
        self.logger.debug(
            'Exporting alembic cache with arguments: {}'.format(alembicJobArgs)
        )
        cmds.AbcExport(j=alembicJobArgs)

        if selectednodes:
            cmds.select(selectednodes)

        return [new_file_path]


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    ma_plugin = MayaAbcPublisherExporterPlugin(api_object)
    ma_plugin.register()
