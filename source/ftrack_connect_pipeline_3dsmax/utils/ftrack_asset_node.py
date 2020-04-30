import ftrack

import MaxPlus

from ftrack_connect_pipeline_3dsmax.constants import FTRACK_ASSET_HELPER_CLASS_ID
import custom_commands as max_utils

import logging
logger = logging.getLogger(__name__)

def is_ftrack_asset_helper(node):
    '''Return True if the node is a Ftrack asset helper node.'''
    if node.Object.ClassID == FTRACK_ASSET_HELPER_CLASS_ID:
        return True

    return False

class FtrackAssetNode(object):
    def __init__(
            self, asset_info, asset_import_mode=None
    ):
        super(FtrackAssetNode, self).__init__()

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

        # if self.asset_take == '3dsmax':
        #     self.helper_object.ParameterBlock.asset_import_mode.Value = self.asset_import_mode

    def _get_unique_ftrack_asset_node_name(self, asset_name):
        return max_utils.get_unique_node_name('{}_ftrackdata'.format(asset_name))

    def connect_to_ftrack_node(self, obj):
        max_utils.deselect_all()
        max_utils.eval_max_script('select {}'.format(obj))
        self._cleanup_selection_and_group_under_ftrack_node()
        #ToDo: add the reimport scene function

    def create_node(self):
        name = self._get_unique_ftrack_asset_node_name(self.asset_name)
        self.node = MaxPlus.Factory.CreateNode(self.helper_object)
        self.node.Name = name
        self.nodes.append(self.node)

        # Try to freeze the helper object and lock the transform.
        try:
            cmd = 'freeze ${0} ; setTransformLockFlags ${0} #all'.format(
                self.asset_name)
            max_utils.eval_max_script(cmd)
        except:
            logger.debug("Could not freeze object {0}".format(self.asset_name))

        return self._update_ftrack_asset_node()

    def _update_ftrack_asset_node(self):
        '''Update the parameters of a Ftrack asset helper.'''

        try:
            cmd = 'unfreeze ${0}'.format(self.node.Name)
            max_utils.eval_max_script(cmd)
        except:
            logger.debug(
                "Could not unfreeze object {0}".format(self.node.Name))

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
            logger.debug(
                "Could not freeze object {0}".format(self.node.Name))
        return self.node

    def _get_asset_id_from_helper_node(self, helperNode):
        assetVersId = helperNode.Object.ParameterBlock.assetId.Value
        vers = ftrack.AssetVersion(id=assetVersId)
        return vers.getAsset().getId()

    def _cleanup_selection_and_group_under_ftrack_node(self):
        asset_id = self.version_id
        root_node = MaxPlus.Core.GetRootNode()

        nodes_to_delete = []

        logger.debug(u'Removing duplicated asset helper objects')
        for node in MaxPlus.SelectionManager.Nodes:
            if is_ftrack_asset_helper(node) and node.Parent == root_node:
                helper_asset_id = self._get_asset_id_from_helper_node(node)
                if helper_asset_id == asset_id:
                    logger.debug(
                        u'Deleting imported helper node {0}'.format(node.Name))
                    nodes_to_delete.append(node)

        # Delete helper nodes that represent the asset we are importing.
        for node in nodes_to_delete:
            MaxPlus.SelectionManager.DeSelectNode(node)
            node.Delete()

        logger.debug(u'Parenting objects to helper object')
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