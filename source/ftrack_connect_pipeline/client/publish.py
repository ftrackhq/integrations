#! /usr/bin/env python
# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import sys
import os

deps_paths = os.environ.get('PYTHONPATH', '').split(os.pathsep)
for path in deps_paths:
    sys.path.append(path)

from ftrack_connect_pipeline import constants
from ftrack_connect_pipeline.client import BasePipelineClient


class PipelinePublisher(BasePipelineClient):

    def __init__(self, ui, host, hostid=None):
        super(PipelinePublisher, self).__init__(ui, host, hostid)
        self.fetch_publisher_definitions()

    def fetch_publisher_definitions(self):
        '''fetch the publishers definitions.'''
        self._fetch_defintions("publisher", self._publishers_loaded)

    def _publishers_loaded(self, event):
        '''event callback for when the publishers are loaded.'''
        raw_data = event['data']

        for item_name, item in raw_data.items():
            print item_name, item
            #self.combo.addItem(item_name, item)

    def _on_publisher_changed(self, index):
        '''Slot triggered on asset type change.'''
        pass

    #TODO: Change this to on publish or something like that to publish its important because
    # it sends the schema to the host
    def _on_run(self):
        '''super(PipelinePublisher, self)._on_run()
        self._update_publish_data()
        self.send_to_host(self.schema, constants.PIPELINE_RUN_HOST_PUBLISHER)'''


'''if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    wid = PipelinePublisher(ui=constants.UI, host=constants.HOST)
    wid.show()
    sys.exit(app.exec_())'''
