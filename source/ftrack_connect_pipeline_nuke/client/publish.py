# # :coding: utf-8
# # :copyright: Copyright (c) 2019 ftrack

from ftrack_connect_pipeline_qt.client.publish import QtPublisherClient
import ftrack_connect_pipeline.constants as constants
import ftrack_connect_pipeline_qt.constants as qt_constants
import ftrack_connect_pipeline_nuke.constants as nuke_constants


class NukePublisherClient(QtPublisherClient):
    ui = [constants.UI, qt_constants.UI, nuke_constants.UI]

    '''Dockable maya load widget'''
    def __init__(self, event_manager, parent=None):
        super(NukePublisherClient, self).__init__(
            event_manager=event_manager, parent=parent
        )
        self.setWindowTitle('Nuke Pipeline Publisher')

    # def show(self):
    #     super(NukePublisherClient, self).show(
    #         dockable=True, floating=False, area='right',
    #         width=200, height=300, x=300, y=600
    # )
