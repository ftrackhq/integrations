# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

import logging

from ftrack_connect_pipeline.asset.dcc_object import DccObject
from ftrack_connect_pipeline import utils as core_utils
from ftrack_connect_pipeline_3dsmax.constants import asset as asset_const
from ftrack_connect_pipeline_3dsmax import utils as max_utils

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
        # Get internal 3dMax dcc object
        dcc_object_node = rt.getNodeByName(self.name, exact=True)
        # Get the Max Dcc object
        if not dcc_object_node:
            self.logger.warning(
                'Could not find MaxDccObject with name {}'.format(self.name)
            )
            return
        # Unfreeze the object to enable modifications
        try:
            rt.unfreeze(dcc_object_node)
        except:
            self.logger.debug(
                "Could not unfreeze object {0}".format(self.name)
            )
        if str(k) == asset_const.REFERENCE_OBJECT:
            rt.setProperty(
                dcc_object_node, k, core_utils.safe_string(self.name)
            )
        elif str(k) in [
            asset_const.IS_LATEST_VERSION,
            asset_const.OBJECTS_LOADED,
        ]:
            rt.setProperty(dcc_object_node, k, bool(v))
        elif str(k) == asset_const.DEPENDENCY_IDS:
            rt.setProperty(
                dcc_object_node, k, core_utils.safe_string(','.join(v or []))
            )
        else:
            rt.setProperty(dcc_object_node, k, v)

        # Freeze the object to make sure no one make modifications on it.
        try:
            rt.freeze(dcc_object_node)
        except Exception as e:
            self.logger.debug(
                "Could not freeze object {0}, Error: {1}".format(
                    dcc_object_node.Name, e
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

        # Create internal Max Dcc object
        dcc_object_node = rt.FtrackAssetHelper()
        dcc_object_node.Name = name

        # Try to freeze the helper object and lock the transform.
        try:
            rt.freeze(dcc_object_node)
            rt.setTransformLockFlags(dcc_object_node, rt.name("all"))
        except Exception as e:
            self.logger.debug(
                "Could not freeze object {0}, Error: {1}".format(name, e)
            )

        self.logger.debug('Creating new dcc object {}'.format(dcc_object_node))
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
        for dcc_object_node in ftrack_asset_nodes:
            id_value = rt.getProperty(
                dcc_object_node, asset_const.ASSET_INFO_ID
            )
            if id_value == asset_info_id:
                self.logger.debug(
                    'Found existing object: {}'.format(dcc_object_node.Name)
                )
                self.name = dcc_object_node.Name
                return self.name

        self.logger.warning(
            "Couldn't find an existing object for the asset info id: {}".format(
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
        dcc_object_node = rt.getNodeByName(object_name, exact=True)
        # Get the Max Dcc object
        if not dcc_object_node:
            error_message = "{} Object doesn't exists".format(object_name)
            logger.error(error_message)
            return param_dict
        # Get properties from the object
        for attr in rt.getPropNames(dcc_object_node):
            value = rt.getProperty(dcc_object_node, attr)
            if attr == asset_const.DEPENDENCY_IDS:
                if len(value) > 0:
                    value = value.split(',')
                else:
                    value = []
            param_dict[str(attr)] = value
        return param_dict

    def is_dcc_object(self, object):
        '''
        Checks if the given *object* has the same ClassID as the
        current ftrack_plugin_id
        '''
        if tuple(object.ClassID) == self.ftrack_plugin_id:
            return True

        return False

    def connect_objects(self, objects):
        '''
        Link the given *objects* ftrack attribute to the self
        :obj:`name` object asset_link attribute in max.

        *objects* List of Max DAG objects
        '''

        # Get DCC object
        dcc_object_node = rt.getNodeByName(self.name, exact=True)

        # Set all connected objects to Asset link attribute for reference.
        # And set dcc_object name to ftrack attribute of all the objects.
        # Always query from the custom ftrack attribute of the objects and not
        # from the asset link, as it is not a live connection, so the
        # asset_link names could be wrong, but the dcc_object id can't be
        # changed, so we can relay on it.

        # Create the custom attribute command.
        attr_command = '''attributes "CustomFtrackAttr"
            (
                parameters pblock
                    (
                        ftrack type:#string default:""
                    )
            )'''

        id_value = rt.getProperty(dcc_object_node, asset_const.ASSET_INFO_ID)

        max_utils.deselect_all()
        for obj in objects:
            # Make sure ftrack attribute is created
            if not rt.isProperty(obj, "ftrack"):
                # Exacute the attr command
                attr = rt.execute(attr_command)
                # Add the custom command to the object
                rt.custAttributes.add(obj.baseObject, attr)
            # Set the asset info id as value for the ftrack attribute
            rt.setProperty(obj, "ftrack", str(id_value))
            # Just for reference, set the name of the current obeject to
            # the asset_link
            # TODO: Check if 3dsmax has a unique id for the objects, and in case,
            # set that id to the asset_link attribute instead of the name.
            rt.setProperty(
                dcc_object_node, asset_const.ASSET_LINK, str(obj.Name)
            )

            self.logger.debug(
                'Node {} added to dcc_object {}'.format(obj, dcc_object_node)
            )
