# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

from ftrack_connect_pipeline.asset import FtrackAssetInfo, FtrackObjectManager
from ftrack_connect_pipeline_maya.constants import asset as asset_const
from ftrack_connect_pipeline_maya.asset.dcc_object import MayaDccObject


class MayaFtrackObjectManager(FtrackObjectManager):
    '''
    Base class to manage FtrackAssetNode object in the maya scene.
    '''

    @property
    def objects_loaded(self):
        '''
        Returns If the asset is loaded
        '''
        return self.asset_info[asset_const.OBJECTS_LOADED]

    @objects_loaded.setter
    def objects_loaded(self, value):
        '''
        Set the self :obj:`asset_info` as loaded and update the attributes in
        the current self :obj:`dcc_object` if exists.

        *loaded* True if the objects are loaded in the scene.
        '''
        self.asset_info[asset_const.OBJECTS_LOADED] = value
        if self.dcc_object:
            self.dcc_object.objects_loaded = value

    def __init__(self, event_manager):
        '''
        Initialize FtrackAssetNode with *event_manager*.

        *event_manager* instance of
        :class:`ftrack_connect_pipeline.event.EventManager`
        '''
        super(MayaFtrackObjectManager, self).__init__(event_manager)

    def _check_sync(self, dcc_object):
        '''
        Check if the parameters of the given *dcc_object* match the
        values of the current self :obj:`asset_info`.
        '''
        # Using == None because it can be an empty dictionary.
        if dcc_object == None:
            error_message = "dcc_object is not set"
            raise AttributeError(error_message)

        synced = False

        node_asset_info = FtrackAssetInfo(dcc_object)

        if node_asset_info == self.asset_info:
            self.logger.debug("{} is synced".format(dcc_object.name))
            synced = True

        return synced

    def _sync(self, dcc_object):
        '''
        Updates the parameters of the given *dcc_object* based on the
        self :obj:`asset_info`.
        '''
        dcc_object.update(self.asset_info)

    def connect_objects(self, objects):
        '''
        Link the given *objects* ftrack attribute to the self
        :obj:`dcc_object` asset_link attribute in maya.

        *objects* List of Maya DAG objects
        '''
        self.dcc_object.connect_objects(objects)

    def create_new_dcc_object(self):
        '''
        Creates a new dcc_object with a unique name.
        '''
        name = self._generate_dcc_object_name()
        dcc_object = MayaDccObject(name)

        self.dcc_object = dcc_object

        return self.dcc_object
