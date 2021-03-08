# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

import json
import six
import base64
from ftrack_connect_pipeline.asset import FtrackAssetInfo, FtrackAssetBase
from ftrack_connect_pipeline_3dsmax.constants import asset as asset_const
from ftrack_connect_pipeline_3dsmax.constants.asset import modes as load_const
import ftrack_connect_pipeline_3dsmax.utils.custom_commands as max_utils
from pymxs import runtime as rt

class FtrackAssetNode(FtrackAssetBase):
    '''
    Base FtrackAssetNode class.
    '''

    identity = asset_const.FTRACK_ASSET_CLASS_ID#MaxPlus.Class_ID(*asset_const.FTRACK_ASSET_CLASS_ID)

    def is_ftrack_object(self, object):
        '''
        Checks if the given object *other* has the same ClassID as the
        current identity
        '''
        if object.ClassID == self.identity:
            return True

        return False

    def is_sync(self, ftrack_object):
        '''Returns bool if the current ftrack_object is sync'''
        return self._check_ftrack_object_sync(ftrack_object)

    def __init__(self, event_manager):
        '''
        Initialize FtrackAssetNode with *event_manager*.

        *event_manager* instance of
        :class:`ftrack_connect_pipeline.event.EventManager`
        '''
        super(FtrackAssetNode, self).__init__(event_manager)

        # self.helper_object = rt.FtrackAssetHelper()
        # self.logger.debug(
        #     'helper_object {} has been created'.format(self.helper_object)
        # )

    def init_ftrack_object(self):
        '''
        Return the ftrack_object for this class. It checks if there is
        already a matching ftrack_object in the scene, in this case, it
        updates the ftrack_object if it's not. In case there is no ftrack_object
        in the scene this function creates a new one.
        '''
        ftrack_object = self.get_ftrack_object_from_scene()
        if not ftrack_object:
            ftrack_object = self.create_new_ftrack_object()
        if ftrack_object:
            if not self.is_sync(ftrack_object):
                ftrack_object = self._update_ftrack_object(ftrack_object)

        self.ftrack_object = ftrack_object

        return self.ftrack_object

    @staticmethod
    def get_parameters_dictionary(max_obj):
        '''
        Returns a diccionary with the keys and values of the given *max_obj*
        parameters
        '''
        param_dict = {}
        for p in rt.getPropNames(max_obj):
            if str(p) == 'Dummy':
                continue
            param_dict[str(p)] = rt.getProperty(max_obj, p)
        return param_dict

    def get_ftrack_object_from_scene(self):
        '''
        Return the ftrack_object from the current asset_version if it exists in
        the scene.
        '''
        ftrack_asset_nodes = max_utils.get_ftrack_helpers()
        for ftrack_object in ftrack_asset_nodes:
            obj = ftrack_object

            param_dict = self.get_parameters_dictionary(obj)
            node_asset_info = FtrackAssetInfo(param_dict)

            if node_asset_info.is_deprecated:
                raise DeprecationWarning("Can not read v1 ftrack asset plugin")
            if (
                    node_asset_info[asset_const.REFERENCE_OBJECT] ==
                    self.asset_info[asset_const.REFERENCE_OBJECT]
            ):

                return ftrack_object

    def _check_ftrack_object_sync(self, ftrack_object):
        '''
        Check if the current parameters of the ftrack_object match the values
        of the asset_info.
        '''
        if not ftrack_object:
            self.logger.warning("Can't check if ftrack ftrack_object is not loaded")
            return False

        synced = False
        obj = ftrack_object

        param_dict = self.get_parameters_dictionary(obj)
        node_asset_info = FtrackAssetInfo(param_dict)

        if node_asset_info == self.asset_info:
            self.logger.debug("{} is synced".format(ftrack_object))
            synced = True

        return synced

    def _get_unique_ftrack_object_name(self):
        '''
        Return a unique scene name for the current ftrack_object
        '''
        ftrack_object_name = super(
            FtrackAssetNode, self
        )._get_unique_ftrack_object_name()

        return max_utils.get_unique_node_name(ftrack_object_name)

    def connect_objects(self, objects):
        '''
        Parent the given *objects* under current ftrack_object

        *objects* is List type of INode
        '''

        max_utils.deselect_all()
        for obj in objects:
            max_utils.add_node_to_selection(obj)
        self._connect_selection()
        if (
                self.asset_info[asset_const.LOAD_MODE] !=
                load_const.SCENE_XREF_MODE
        ):
            self.reload_references_from_selection()

    def get_load_mode_from_ftrack_object(self, node):
        '''Return the load mode used to import an asset.'''
        obj = node
        return obj.asset_info_options

    def reload_references_from_selection(self):
        '''
        Reload all the ftrack dependencies that are referenced in the current
        selection.
        '''
        for node in rt.GetCurrentSelection():
            if self.is_ftrack_object(node) and self.get_load_mode_from_ftrack_object(
                    node) == load_const.SCENE_XREF_MODE:
                if not max_utils.scene_XRef_imported(node):
                    self.logger.debug(u'Re-importing {0} scene xref.'.format(
                        node.Name))
                    max_utils.re_import_scene_XRef(
                        node.component_path,
                        node.Name
                    )

    def create_new_ftrack_object(self):
        '''
        Creates a ftrack_object with a unique name. The ftrack_object is
        type of FtrackAssetHelper.
        '''
        name = self._get_unique_ftrack_object_name()
        ftrack_object = rt.FtrackAssetHelper()
        ftrack_object.Name = name

        # Try to freeze the helper object and lock the transform.
        try:
            rt.freeze(ftrack_object)
            rt.setTransformLockFlags(ftrack_object, rt.name("all"))
        except Exception as e:
            self.logger.debug(
                "Could not freeze object {0}, Error: {1}".format(
                    self.asset_info['asset_name'], e
                )
            )

        return ftrack_object

    def _update_ftrack_object(self, ftrack_object):
        '''Update the parameters of the ftrack_object. And Return the
        ftrack_object updated
        '''
        try:
            rt.unfreeze(ftrack_object)
        except:
            self.logger.debug(
                "Could not unfreeze object {0}".format(ftrack_object.Name))

        obj = ftrack_object

        for p in rt.getPropNames(obj):
            if str(p) == 'Dummy':
                continue
            if str(p) == asset_const.REFERENCE_OBJECT:
                rt.setProperty(obj, p, str(ftrack_object))
            elif str(p) == asset_const.VERSIONS:
                continue
            elif str(p) == asset_const.IS_LATEST_VERSION:
                rt.setProperty(obj, p, bool(self.asset_info[str(p)]))
            elif str(p) == asset_const.SESSION:
                rt.setProperty(obj, p, str(self.asset_info[str(p)]))
            elif str(p) == asset_const.ASSET_INFO_OPTIONS:
                decoded_value = self.asset_info[str(p)]
                json_data = json.dumps(decoded_value)
                if six.PY2:
                    encoded_value = base64.b64encode(json_data)
                else:
                    input_bytes = json_data.encode('utf8')
                    encoded_value = base64.b64encode(input_bytes).decode('ascii')
                rt.setProperty(
                    obj, p, str(encoded_value)
                )
            else:
                rt.setProperty(obj, p, self.asset_info[str(p)])

        try:
            rt.freeze(ftrack_object)
        except Exception as e:
            self.logger.debug(
                "Could not freeze object {0}, Error: {1}".format(
                    ftrack_object.Name, e
                )
            )
        return ftrack_object

    def _get_component_id_from_helper_node(self, helper_node):
        '''
        Return component_id of the given *helperNode*.
        '''
        component_id = helper_node.component_id
        return component_id

    def _get_version_id_from_helper_node(self, helper_node):
        '''
        Return version_id of the given *helperNode*.
        '''
        version_id = helper_node.version_id
        return version_id

    def _connect_selection(self):
        '''
        Removes pre existing asset helper objects and parent the selected
        nodes to the current ftrack_object.
        '''
        version_id = self.asset_info[asset_const.VERSION_ID]
        component_id = self.asset_info[asset_const.COMPONENT_ID]
        root_node = rt.rootScene.world

        nodes_to_delete = []

        self.logger.debug(u'Removing duplicated asset helper objects')
        for node in rt.selection:
            if self.is_ftrack_object(node) and node.Parent == root_node:
                helper_component_id = self._get_component_id_from_helper_node(node)
                if helper_component_id == component_id:
                    self.logger.debug(
                        u'Deleting imported helper ftrack_object {0}'.format(node.Name))
                    nodes_to_delete.append(node)

        # Delete helper ftrack_objects that represent the asset we are importing.
        for node in nodes_to_delete:
            rt.deselect(node)
            rt.delete(node)

        self.logger.debug(u'Parenting objects to helper object')
        for node in rt.GetCurrentSelection():
            if node.Parent == root_node or node.Parent == None:
                node.Parent = self.ftrack_object
                self.logger.debug(
                    'ftrack_object {} added to ftrack ftrack_object {}'.format(
                        node, self.ftrack_object
                    )
                )

