import ftrack

import MaxPlus

from ftrack_connect_pipeline_3dsmax.constants import FTRACK_ASSET_HELPER_CLASS_ID
import custom_commands as max_utils

import logging

def is_ftrack_asset_helper(node):
    '''Return True if the node is a Ftrack asset helper node.'''
    if node.Object.ClassID == FTRACK_ASSET_HELPER_CLASS_ID:
        return True

    return False

class FtrackAssetNode(object):
    '''
        Base FtrackAssetNode class.
    '''
    def __init__(
            self, asset_info, asset_import_mode=None
    ):
        '''
            Initialize FtrackAssetNode with *asset_info*, and optional
            *asset_import_mode*.

            *asset_info* Dictionary with the current asset information from
            ftrack. Needed keys: asset_name, version_number, context_id,
            asset_type, asset_id, version_id, component_name, component_id,
            compoennt_path.
        '''
        super(FtrackAssetNode, self).__init__()

        self.logger = logging.getLogger(__name__)

        self.nodes = []
        self.node = None

        self.asset_name = asset_info.get('asset_name')
        self.version_number = asset_info.get('version_number')
        self.context_id = asset_info.get('context_id')
        self.asset_type = asset_info.get('asset_type')
        self.asset_id = asset_info.get('asset_id')
        self.version_id = asset_info.get('version_id')
        self.component_name = asset_info.get('component_name')
        self.component_id = asset_info.get('component_id')
        self.component_path = asset_info.get('component_path')

        self.asset_import_mode = asset_import_mode

        self.helper_object = MaxPlus.Factory.CreateHelperObject(
            FTRACK_ASSET_HELPER_CLASS_ID
        )
        self.logger.debug(
            'helper_object {} has been created'.format(self.helper_object)
        )

        # if self.asset_take == '3dsmax':
        #     self.helper_object.ParameterBlock.asset_import_mode.Value = self.asset_import_mode

    def _get_unique_ftrack_asset_node_name(self, asset_name):
        '''
        Return a unique scene name for the given *asset_name*
        '''
        return max_utils.get_unique_node_name('{}_ftrackdata'.format(asset_name))

    def connect_to_ftrack_node(self, obj):
        '''
        Parent the given *obj* under current ftrack_node

        *obj* is type of INode
        '''
        max_utils.deselect_all()
        max_utils.add_node_to_selection(obj)
        self._cleanup_selection_and_group_under_ftrack_node()
        self.logger.debug(
            'Object {} has been connected to {}'.format(obj, self.node)
        )
        #ToDo: add the reimport scene function

    def create_node(self):
        '''
        Creates the ftrack_node with a unique name. The ftrack node is type of
        FtrackAssetHelper.

        '''
        name = self._get_unique_ftrack_asset_node_name(self.asset_name)
        self.node = MaxPlus.Factory.CreateNode(self.helper_object)
        self.node.Name = name
        self.nodes.append(self.node)

        # Try to freeze the helper object and lock the transform.
        try:
            cmd = 'freeze ${0} ; setTransformLockFlags ${0} #all'.format(
                self.node.Name)
            max_utils.eval_max_script(cmd)
        except:
            self.logger.debug("Could not freeze object {0}".format(self.asset_name))

        return self._update_ftrack_asset_node()

    def _update_ftrack_asset_node(self):
        '''Update the parameters of the ftrack node. And Return the ftrack node
        updated
        '''

        try:
            cmd = 'unfreeze ${0}'.format(self.node.Name)
            max_utils.eval_max_script(cmd)
        except:
            self.logger.debug(
                "Could not unfreeze object {0}".format(self.node.Name))

        #TODO: update the ftrack_node parameter names to match what they currently are
        obj = self.node.Object
        obj.ParameterBlock.assetId.Value = self.version_id
        obj.ParameterBlock.assetVersion.Value = int(self.version_number)
        obj.ParameterBlock.assetPath.Value = self.component_path
        obj.ParameterBlock.assetTake.Value = self.component_name
        obj.ParameterBlock.assetType.Value = self.asset_type
        obj.ParameterBlock.assetComponentId.Value = self.component_id

        try:
            cmd = 'freeze ${0}'.format(self.node.Name)
            max_utils.eval_max_script(cmd)
        except:
            self.logger.debug(
                "Could not freeze object {0}".format(self.node.Name))
        return self.node

    def _get_asset_id_from_helper_node(self, helperNode):
        '''
        Find the asset version id added on the given *helperNode*. Then gets
        the asset version object from ftrack and Return the asset id of this
        asset version
        '''
        assetVersId = helperNode.Object.ParameterBlock.assetId.Value
        vers = ftrack.AssetVersion(id=assetVersId)
        return vers.getAsset().getId()

    def _cleanup_selection_and_group_under_ftrack_node(self):
        '''
        Removes pre existing asset helper objects and parent the selected nodes
        to the current ftrack node.
        '''
        asset_id = self.version_id
        root_node = MaxPlus.Core.GetRootNode()

        nodes_to_delete = []

        self.logger.debug(u'Removing duplicated asset helper objects')
        for node in MaxPlus.SelectionManager.Nodes:
            if is_ftrack_asset_helper(node) and node.Parent == root_node:
                helper_asset_id = self._get_asset_id_from_helper_node(node)
                if helper_asset_id == asset_id:
                    self.logger.debug(
                        u'Deleting imported helper node {0}'.format(node.Name))
                    nodes_to_delete.append(node)

        # Delete helper nodes that represent the asset we are importing.
        for node in nodes_to_delete:
            MaxPlus.SelectionManager.DeSelectNode(node)
            node.Delete()

        self.logger.debug(u'Parenting objects to helper object')
        for node in MaxPlus.SelectionManager.Nodes:
            if node.Parent == root_node:
                node.Parent = self.node

    # def _reimportSceneXRefs(self):
    #     for node in MaxPlus.SelectionManager.Nodes:
    #         if is_ftrack_asset_helper(node) and getAssetImportMode(node) == SCENE_XREF_IMPORT_MODE:
    #             if not sceneXRefImported(node):
    #                 logger.debug(u'Re-importing {0} scene xref.'.format(
    #                     node.Name))
    #                 reimportSceneXRef(node)