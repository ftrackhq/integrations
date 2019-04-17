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

    def get_sequence_start_end(self, path):
        try:
            if '%V' in path:
                path = path.replace('%V', 'left')
            hashMatch = re.search('#+', path)
            if hashMatch:
                path = path[:hashMatch.start(0)] + '*' + path[hashMatch.end(0):]

            nukeFormatMatch = re.search('%\d+d', path)
            if nukeFormatMatch:
                path = (
                    path[:nukeFormatMatch.start(0)] + '*' +
                    path[nukeFormatMatch.end(0):]
                )

            fileExtension = os.path.splitext(path)[1].replace('.', '\.')
            files = sorted(glob.glob(path))
            regexp = '(\d+)' + fileExtension + ''
            first = int(re.findall(regexp, files[0])[0])
            last = int(re.findall(regexp, files[-1])[0])
        except:
            traceback.print_exc(file=sys.stdout)
            first = 1
            last = 1
        return first, last

    def run(self, context=None, data=None, options=None):
        component_name = options['component_name']
        return {component_name: data[0]}


def register(api_object, **kw):
    plugin = ExtractSequencePlugin(api_object)
    plugin.register()
