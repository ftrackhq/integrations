# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import sys
import tempfile
import os
import glob
import re
import traceback
import nuke

from ftrack_connect_pipeline_nuke import plugin


class ExtractSequencePlugin(plugin.ExtractorNukePlugin):
    plugin_name = 'sequence'

    def run(self, context=None, data=None, options=None):
        component_name = options['component_name']
        return {component_name: data[0]}


def register(api_object, **kw):
    plugin = ExtractSequencePlugin(api_object)
    plugin.register()
