# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

import json
import ftrack_api

from ftrack_connect_pipeline.asset import FtrackAssetInfo, FtrackAssetBase
from ftrack_connect_pipeline_maya.constants import asset as asset_const
from ftrack_connect_pipeline import constants as core_const
from ftrack_connect_pipeline_maya.utils import custom_commands as maya_utils

import maya.cmds as cmd


class FtrackAssetNode(FtrackAssetBase):
    '''
    Base FtrackAssetNode class.
    '''

    def is_sync(self):
        return self._check_ftrack_object_sync()

    def __init__(self, event_manager):
        '''
        Initialize FtrackAssetNode with *ftrack_asset_info*, and *session*.

        *ftrack_asset_info* should be the
        :class:`ftrack_connect_pipeline.asset.asset_info.FtrackAssetInfo`
        instance.
        *session* should be the :class:`ftrack_api.session.Session` instance
        to use for communication with the server.
        '''
        super(FtrackAssetNode, self).__init__(event_manager)

    def init_ftrack_object(self):
        '''
        Return the ftrack ftrack_object for this class. It checks if there is
        already a matching ftrack ftrack_object in the scene, in this case it
        updates the ftrack_object if it's not. In case there is no ftrack_object
        in the scene this function creates a new one.
        '''
        ftrack_object = self.get_ftrack_object_from_scene()
        if ftrack_object:
            self._set_ftrack_object(ftrack_object)
            if not self.is_sync():
                self._update_ftrack_object()
        else:
            self.create_new_ftrack_object()

        return self.ftrack_object

    def _get_parameters_dictionary(self, maya_obj):
        param_dict = {}
        all_attr = cmd.listAttr(maya_obj, c=True, se=True)
        for attr in all_attr:
            if cmd.attributeQuery(attr, node=maya_obj, msg=True):
                continue
            attr_value = cmd.getAttr('{}.{}'.format(maya_obj, attr))
            param_dict[attr] = attr_value
        return param_dict

    def get_ftrack_object_from_scene(self):
        '''
        Return the ftrack ftrack_object of the current asset_version of the
        scene if exists.
        '''
        ftrack_asset_nodes = maya_utils.get_ftrack_nodes()
        for ftrack_object in ftrack_asset_nodes:
            param_dict = self._get_parameters_dictionary(ftrack_object)
            node_asset_info = FtrackAssetInfo(param_dict)
            if node_asset_info.is_deprecated:
                raise DeprecationWarning("Can not read v1 ftrack asset plugin")
            if (
                    node_asset_info[asset_const.REFERENCE_OBJECT] ==
                    self.asset_info[asset_const.REFERENCE_OBJECT]
            ):

                return ftrack_object

    def _check_ftrack_object_sync(self):
        '''
        Check if the current parameters of the ftrack ftrack_object match the
        values of the asset_info.
        '''
        if not self.ftrack_object:
            self.logger.warning(
                "Can't check if ftrack ftrack_object is not loaded"
            )
            return False

        synced = False

        param_dict = self._get_parameters_dictionary(self.ftrack_object)
        node_asset_info = FtrackAssetInfo(param_dict)

        if node_asset_info == self.asset_info:
            self.logger.debug("{} is synced".format(self.ftrack_object))
            synced = True

        return synced

    def _get_unique_ftrack_object_name(self):
        '''
        Return a unique scene name for the current asset_name
        '''
        ftrack_object_name = '{}_ftrackdata'.format(
            self.asset_info[asset_const.ASSET_NAME]
        )
        count = 0
        while 1:
            if cmd.objExists(ftrack_object_name):
                ftrack_object_name = ftrack_object_name + str(count)
                count = count + 1
            else:
                break
        return ftrack_object_name

    def connect_objects(self, objects):
        '''
        Parent the given *objects* under current ftrack_object

        *objects* is List type of INode
        '''
        for obj in objects:
            if cmd.lockNode(obj, q=True)[0]:
                cmd.lockNode(obj, l=False)

            if not cmd.attributeQuery('ftrack', n=obj, exists=True):
                cmd.addAttr(obj, ln='ftrack', at='message')

            if not cmd.listConnections('{}.ftrack'.format(obj)):
                cmd.connectAttr(
                    '{}.{}'.format(self.ftrack_object, asset_const.ASSET_LINK),
                    '{}.ftrack'.format(obj)
                )

    def get_load_mode_from_ftrack_object(self, obj):
        '''Return the import mode used to import an asset.'''
        load_mode = cmd.getAttr('{}.{}'.format(
            obj, asset_const.LOAD_MODE)
        )
        return load_mode

    def create_new_ftrack_object(self):
        '''
        Creates the ftrack_node with a unique name. The ftrack ftrack_object is
        type of FtrackAssetHelper.

        '''

        name = self._get_unique_ftrack_object_name()
        self._ftrack_object = cmd.createNode('ftrackAssetNode', name=name)
        self._ftrack_objects.append(self.ftrack_object)

        return self._update_ftrack_object()

    def _update_ftrack_object(self):
        '''Update the parameters of the ftrack ftrack_object. And Return the
        ftrack ftrack_object updated
        '''
        for k, v in self.asset_info.items():
            cmd.setAttr('{}.{}'.format(self.ftrack_object, k), l=False)
            if k == asset_const.VERSION_NUMBER:
                cmd.setAttr('{}.{}'.format(self.ftrack_object, k), v, l=True)
            elif k == asset_const.REFERENCE_OBJECT:
                cmd.setAttr(
                    '{}.{}'.format(
                        self.ftrack_object, k
                    ), str(self.ftrack_object), type="string", l=True
                )
            else:
                cmd.setAttr('{}.{}'.format(
                    self.ftrack_object, k), v, type="string", l=True
                )

        return self.ftrack_object

    def _change_version(self, event):
        '''
        Override function from the main class, remove the current assets of the
        scene and loads the given version of the asset in the *event*. Then
        super the base function.
        '''
        asset_info = event['data']

        try:
            self.logger.debug("Removing current objects")
            self.remove_current_objects()
        except Exception, e:
            self.logger.error("Error removing current objects: {}".format(e))


        asset_info_options = json.loads(
            self.asset_info[asset_const.ASSET_INFO_OPTIONS].decode('base64')
        )

        asset_context = asset_info_options['settings']['context']
        asset_data = asset_info[asset_const.COMPONENT_PATH]
        asset_context[asset_const.ASSET_ID] = asset_info[asset_const.ASSET_ID]
        asset_context[asset_const.VERSION_NUMBER] = asset_info[asset_const.VERSION_NUMBER]
        asset_context[asset_const.ASSET_NAME] = asset_info[asset_const.ASSET_NAME]
        asset_context[asset_const.ASSET_TYPE] = asset_info[asset_const.ASSET_TYPE]
        asset_context[asset_const.VERSION_ID] = asset_info[asset_const.VERSION_ID]

        asset_info_options['settings']['data'] = [asset_data]
        asset_info_options['settings']['context'].update(asset_context)

        run_event = ftrack_api.event.base.Event(
            topic=core_const.PIPELINE_RUN_PLUGIN_TOPIC,
            data=asset_info_options
        )
        plugin_result_data = self.session.event_hub.publish(
            run_event,
            synchronous=True
        )
        result_data = plugin_result_data[0]
        if not result_data:
            self.logger.error("Error re-loading asset")

        event['data'][asset_const.ASSET_INFO_OPTIONS] = json.dumps(
            asset_info_options
        ).encode('base64')
        event['data'][asset_const.LOAD_MODE] = self.asset_info[
            asset_const.LOAD_MODE
        ]
        event['data'][asset_const.REFERENCE_OBJECT] = self.asset_info[
            asset_const.REFERENCE_OBJECT
        ]
        super(FtrackAssetNode, self)._change_version(event)

    def discover_assets(self):
        '''
        Returns *asset_info_list* with all the assets loaded in the current
        scene that has an ftrackAssetNode connected
        '''
        ftrack_asset_nodes = maya_utils.get_ftrack_nodes()
        asset_info_list = []

        for ftrack_object in ftrack_asset_nodes:
            param_dict = self._get_parameters_dictionary(ftrack_object)
            node_asset_info = FtrackAssetInfo(param_dict)
            asset_info_list.append(node_asset_info)
        return asset_info_list

    def remove_current_objects(self):
        '''
        Remove all the imported or referenced objects in the scene
        '''
        referenceNode = False
        for node in cmd.listConnections(
                '{}.{}'.format(self.ftrack_object, asset_const.ASSET_LINK)
        ):
            if cmd.nodeType(node) == 'reference':
                referenceNode = maya_utils.getReferenceNode(node)
                if referenceNode:
                    break

        if referenceNode:
            self.logger.debug("Removing reference: {}".format(referenceNode))
            maya_utils.remove_reference_node(referenceNode)
        else:
            nodes = cmd.listConnections(
                '{}.{}'.format(self.ftrack_object, asset_const.ASSET_LINK)
            )
            for node in nodes:
                try:
                    self.logger.debug(
                        "Removing object: {}".format(node)
                    )
                    if cmd.objExists(node):
                        cmd.delete(node)
                except Exception as error:
                    self.logger.error(
                        'Node: {0} could not be deleted, error: {1}'.format(
                            node, error
                        )
                    )
        if cmd.objExists(self.ftrack_object):
            cmd.delete(self.ftrack_object)

    def _remove_asset(self, event):
        '''
        Override function from the main class, remove the current assets of the
        scene.
        '''
        super(FtrackAssetNode, self)._remove_asset(event)

        asset_item = event['data']

        try:
            self.logger.debug("Removing current objects")
            self.remove_current_objects()
        except Exception, e:
            self.logger.error("Error removing current objects: {}".format(e))

        return asset_item

    def _select_asset(self, event):
        '''
        Override function from the main class, select the current assets of the
        scene.
        '''
        super(FtrackAssetNode, self)._select_asset(event)
        asset_item = event['data']

        nodes = cmd.listConnections(
            '{}.{}'.format(self.ftrack_object, asset_const.ASSET_LINK)
        )
        for node in nodes:
            cmd.select(node, add=True)

        return asset_item

    def _clear_selection(self, event):
        '''
        Override function from the main class, select the current assets of the
        scene.
        '''
        super(FtrackAssetNode, self)._clear_selection(event)
        asset_item = event['data']

        cmd.select(cl=True)

        return asset_item