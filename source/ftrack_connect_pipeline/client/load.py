#! /usr/bin/env python
# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import os
import sys

deps_paths = os.environ.get('PYTHONPATH', '').split(os.pathsep)
for path in deps_paths:
    sys.path.append(path)


from ftrack_connect_pipeline import constants
from ftrack_connect_pipeline.client import BasePipelineClient


class PipelineLoader(BasePipelineClient):
    '''
    Base load widget class.
    '''
    def __init__(self, ui, host, hostid=None):

        super(PipelineLoader, self).__init__(ui, host, hostid)


'''if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    wid = QtPipelineLoaderWidget(ui=constants.UI, host=constants.HOST)
    wid.show()
    sys.exit(app.exec_())'''
