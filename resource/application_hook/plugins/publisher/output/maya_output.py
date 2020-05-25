# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import tempfile

import maya.cmds as cmd
import maya

from ftrack_connect_pipeline_maya import plugin



class OutputMayaPlugin(plugin.PublisherOutputMayaPlugin):

    extension = None
    filetype = None

    def extract_options(self, options):

        return {
            'op': 'v=0',
            'typ': self.filetype,
            'constructionHistory' : bool(options.get('history', False)),
            'channels' : bool(options.get('channels', False)),
            'preserveReferences' : bool(options.get('preserve_reference', False)),
            'shader' : bool(options.get('shaders', False)),
            'constraints' : bool(options.get('constraints', False)),
            'expressions' : bool(options.get('expressions', False)),
            'exportSelected': True,
            'exportAll':False,
            'force': True
        }

    def run(self, context=None, data=None, options=None):
        component_name = options['component_name']
        new_file_path = tempfile.NamedTemporaryFile(
            delete=False,
            suffix=self.extension
        ).name

        options = self.extract_options(options)

        self.logger.debug(
            'Calling output options: data {}. options {}'.format(
                data, options
            )
        )

        cmd.select(data, r=True)
        cmd.file(
            new_file_path,
            **options
        )

        return {component_name: new_file_path}


class OutputMayaAsciiPlugin(OutputMayaPlugin):
    plugin_name = 'maya_ascii'
    extension = '.ma'
    filetype = 'mayaAscii'


class OutputMayaBinaryPlugin(OutputMayaPlugin):
    plugin_name = 'maya_binary'
    extension = '.mb'
    filetype = 'mayaBinary'


def register(api_object, **kw):
    ma_plugin = OutputMayaAsciiPlugin(api_object)
    mb_plugin = OutputMayaBinaryPlugin(api_object)
    ma_plugin.register()
    mb_plugin.register()
