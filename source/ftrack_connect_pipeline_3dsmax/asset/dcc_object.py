# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

import logging

from ftrack_connect_pipeline.asset.dcc_object import DccObject
from ftrack_connect_pipeline_3dsmax.constants import asset as asset_const
from ftrack_connect_pipeline_3dsmax.utils import custom_commands as max_utils

from pymxs import runtime as rt


class MaxDccObject(DccObject):
    '''MaxDccObject class.'''

    ftrack_plugin_id = asset_const.FTRACK_PLUGIN_ID
    '''Plugin id used on some DCC applications '''

    def __init__(self, name=None, from_id=None, **kwargs):
        '''
        If the *from_id* is provided find an object in the dcc with the given
        *from_id* as assset_info_id.
        If a *name* is provided create a new object in the dcc.
        '''
        self.logger = logging.getLogger(
            '{0}.{1}'.format(__name__, self.__class__.__name__)
        )
        super(MaxDccObject, self).__init__(name, from_id, **kwargs)

    def __setitem__(self, k, v):
        '''
        Sets the given *v* into the given *k* and automatically set the
        attributes of the current self :obj:`name` on the DCC
        '''
        dcc_object = rt.getNodeByName(self.name, exact=True)
        # Get the Max Dcc object
        if not dcc_object:
            self.logger.warning(
                'Could not find MaxDccObject with name {}'.format(self.name)
            )
            return
        # Unfreeze the object to enable modifications
        try:
            rt.unfreeze(dcc_object)
        except:
            self.logger.debug(
                "Could not unfreeze object {0}".format(dcc_object.Name))

        if str(k) == asset_const.REFERENCE_OBJECT:
            rt.setProperty(dcc_object, k, str(self.name))
        elif str(k) == asset_const.IS_LATEST_VERSION:
            rt.setProperty(dcc_object, k, bool(v))
        # TODO: Check if this is necesary, shouldnt be.
        # elif str(k) == asset_const.ASSET_INFO_OPTIONS:
        #     decoded_value = self.asset_info[str(k)]
        #     json_data = json.dumps(decoded_value)
        #     if six.PY2:
        #         encoded_value = base64.b64encode(json_data)
        #     else:
        #         input_bytes = json_data.encode('utf8')
        #         encoded_value = base64.b64encode(input_bytes).decode('ascii')
        #     rt.setProperty(
        #         dcc_object, k, str(encoded_value)
        #     )
        else:
            rt.setProperty(dcc_object, k, v)
        # TODO: This might be necessary.
        # elif k == asset_const.DEPENDENCY_IDS:
        #     cmds.setAttr(
        #         '{}.{}'.format(self.name, k),
        #         *([len(v)] + v),
        #         type="stringArray",
        #         l=True
        #     )
        #

        # Freeze the object to make sure no one make modifications on it.
        try:
            rt.freeze(dcc_object)
        except Exception as e:
            self.logger.debug(
                "Could not freeze object {0}, Error: {1}".format(
                    dcc_object.Name, e
                )
            )

        super(MaxDccObject, self).__setitem__(k, v)

    def create(self, name):
        '''
        Creates a new dcc_object with the given *name* if doesn't exists.
        '''
        if self._name_exists(name):
            error_message = "{} already exists in the scene".format(name)
            self.logger.error(error_message)
            raise RuntimeError(error_message)

        dcc_object = rt.FtrackAssetHelper()
        dcc_object.Name = name

        # Try to freeze the helper object and lock the transform.
        try:
            rt.freeze(dcc_object)
            rt.setTransformLockFlags(dcc_object, rt.name("all"))
        except Exception as e:
            self.logger.debug(
                "Could not freeze object {0}, Error: {1}".format(
                    name, e
                )
            )

        self.logger.debug('Creating new dcc object {}'.format(dcc_object))
        self.name = name
        return self.name

    def _name_exists(self, name):
        '''
        Return true if the given *name* exists in the scene.
        '''

        if rt.getNodeByName(name, exact=True):
            return True

        return False

    def from_asset_info_id(self, asset_info_id):
        '''
        Checks max scene to get all the ftrackAssetNode objects. Compares them
        with the given *asset_info_id* and returns them if matches.
        '''
        ftrack_asset_nodes = max_utils.get_ftrack_nodes()
        for dcc_object in ftrack_asset_nodes:

            id_value = rt.getProperty(dcc_object, asset_const.ASSET_INFO_ID)

            if id_value == asset_info_id:
                self.logger.debug(
                    'Found existing object: {}'.format(dcc_object.Name)
                )
                self.name = dcc_object.Name
                return self.name

        self.logger.debug(
            "Couldn't found an existing object for the asset info id: {}".format(
                asset_info_id
            )
        )
        return None

    @staticmethod
    def dictionary_from_object(object_name):
        '''
        Static method to be used without initializing the current class.
        Returns a dictionary with the keys and values of the given
        *object_name* if exists.

        *object_name* ftrackAssetNode object type from max scene.
        '''
        logger = logging.getLogger(
            '{0}.{1}'.format(__name__, __class__.__name__)
        )
        param_dict = {}
        dcc_object = rt.getNodeByName(object_name, exact=True)
        # Get the Max Dcc object
        if not dcc_object:
            error_message = "{} Object doesn't exists".format(object_name)
            logger.error(error_message)
            return param_dict
        # Get properties from the object
        for attr in rt.getPropNames(dcc_object):
            param_dict[str(attr)] = rt.getProperty(dcc_object, attr)
        return param_dict

    def is_dcc_object(self, object):
        '''
        Checks if the given *object* has the same ClassID as the
        current ftrack_plugin_id
        '''
        if object.ClassID == self.ftrack_plugin_id:
            return True

        return False

    def connect_objects(self, objects):
        '''
        Link the given *objects* ftrack attribute to the self
        :obj:`name` object asset_link attribute in max.

        *objects* List of Max DAG objects
        '''

        #Get DCC object
        dcc_object = rt.getNodeByName(self.name, exact=True)

        max_utils.deselect_all()
        for obj in objects:
            max_utils.add_node_to_selection(obj)

        # Get max root node
        root_node = rt.rootScene.world
        # Parent selected nodes to DCCobject
        for node in rt.GetCurrentSelection():
            if node.Parent == root_node or not node.Parent:
                node.Parent = dcc_object
                self.logger.debug(
                    'Node {} added to dcc_object {}'.format(
                        node, dcc_object
                    )
                )