# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import tempfile

import maya.cmds as cmd
import maya

from ftrack_connect_pipeline_maya import plugin


class OutputMayaAsciiPlugin(plugin.OutputMayaPlugin):
    plugin_name = 'mayaascii'

    def run(self, context=None, data=None, options=None):
        component_name = options['component_name']
        new_file_path = tempfile.NamedTemporaryFile(delete=False,
                                                    suffix='.ma').name
        self.logger.debug('Calling extractor options: data {}'.format(data))
        cmd.select(data, r=True)
        cmd.file(rename=new_file_path)
        cmd.file(save=True, type='mayaAscii')
        return {component_name: new_file_path}


def register(api_object, **kw):
    plugin = OutputMayaAsciiPlugin(api_object)
    plugin.register()
