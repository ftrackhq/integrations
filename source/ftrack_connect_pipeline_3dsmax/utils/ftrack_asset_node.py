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
    def __init__(self, context, data, session):
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

        self.context = context
        self.data = data
        self.session = session

        self.asset_info = self._get_asset_info()

        self.helper_object = MaxPlus.Factory.CreateHelperObject(
            FTRACK_ASSET_HELPER_CLASS_ID
        )
        self.logger.debug(
            'helper_object {} has been created'.format(self.helper_object)
        )

        # if self.asset_take == '3dsmax':
        #     self.helper_object.ParameterBlock.asset_import_mode.Value = self.asset_import_mode
    def _get_asset_info(self):
        asset_info = {}

        asset_info['asset_name'] = self.context.get('asset_name', 'No name found')
        asset_info['version_number'] = self.context.get('version_number', '0')
        asset_info['context_id'] = self.context.get('context_id', '')
        asset_info['asset_type'] = self.context.get('asset_type', '')
        asset_info['asset_id'] = self.context.get('asset_id', '')
        asset_info['version_id'] = self.context.get('version_id', '')
        #asset_info['asset_load_mode'] = self.data.get('asset_load_mode', '')

        asset_version = self.session.get(
            'AssetVersion', asset_info['version_id']
        )

        location = self.session.pick_location()

        for component in asset_version['components']:
            if location.get_component_availability(component) < 100.0:
                continue
            component_path = location.get_filesystem_path(component)
            if component_path in self.data:
                asset_info['component_name'] = component['name']
                asset_info['component_id'] = component['id']
                asset_info['component_path'] = component_path

        if asset_info:
            self.logger.debug(
                'asset_info dictionary done : {}'.format(asset_info)
            )
        return asset_info
    def init_ftrack_node(self):
        '''
        Return the ftrack node for this class. It checks if there is already a
        matching ftrack node in the scene, in this case it updates the node if
        it's not. In case there is no node in the scene this function creates a
        new one.
        '''
        ftrack_node = self.get_ftrack_node_from_scene()
        if ftrack_node:
            self.set_ftrack_node(ftrack_node)
            if not self.is_ftrack_node_sync():
                self._update_ftrack_asset_node()

        else:
            self.create_new_node()

        return self.node

    def set_asset_load_mode(self, asset_load_mode):
        self.asset_info['asset_load_mode'] = asset_load_mode

    def get_ftrack_node_from_scene(self):
        '''
        Return the ftrack node of the current asset_version of the scene if
        exists.
        '''
        ftrack_asset_nodes = max_utils.get_ftrack_helpers()
        for ftrack_node in ftrack_asset_nodes:
            obj = ftrack_node.Object
            asset_version_id = obj.ParameterBlock.asset_version_id.Value
            asset_id = obj.ParameterBlock.asset_id.Value
            if (
                    asset_version_id == self.asset_info['version_id'] and
                    asset_id == self.asset_info['asset_id']
            ):
                return ftrack_node

    def set_ftrack_node(self, ftrack_node):
        '''
        Sets the given *ftrack_node* as the current self.node of the class
        '''
        self.node = ftrack_node

    def is_ftrack_node_sync(self):
        '''
        Check if the current parameters of the ftrack node match the parameters
        of the porperty asset_info.

        ..Note:: Checks only the new parameters not the legacy ones

        '''
        if not self.node:
            self.logger.warning("No ftrack node loaded")
            return None

        obj = self.node.Object
        for p in obj.ParameterBlock.Parameters:
            if p.Name in self.asset_info.keys():
                if p.Value != self.asset_info[p.Name]:
                    return False
        return True

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

    def create_new_node(self):
        '''
        Creates the ftrack_node with a unique name. The ftrack node is type of
        FtrackAssetHelper.

        '''
        name = self._get_unique_ftrack_asset_node_name(
            self.asset_info['asset_name']
        )
        self.node = MaxPlus.Factory.CreateNode(self.helper_object)
        self.node.Name = name
        self.nodes.append(self.node)

        # Try to freeze the helper object and lock the transform.
        try:
            cmd = 'freeze ${0} ; setTransformLockFlags ${0} #all'.format(
                self.node.Name)
            max_utils.eval_max_script(cmd)
        except:
            self.logger.debug(
                "Could not freeze object {0}".format(
                    self.asset_info['asset_name']
                )
            )

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

        obj = self.node.Object
        # Setting up the legacy parameters
        obj.ParameterBlock.assetId.Value = self.asset_info['version_id']
        obj.ParameterBlock.assetVersion.Value = int(self.asset_info['version_number'])
        obj.ParameterBlock.assetPath.Value = self.asset_info['component_path']
        obj.ParameterBlock.assetTake.Value = self.asset_info['component_name']
        obj.ParameterBlock.assetType.Value = self.asset_info['asset_type']
        obj.ParameterBlock.assetComponentId.Value = self.asset_info['component_id']
        # Setting up new parameters
        obj.ParameterBlock.asset_id.Value = self.asset_info['asset_id']
        obj.ParameterBlock.asset_version_id.Value = self.asset_info['version_id']
        obj.ParameterBlock.version_number.Value = int(
            self.asset_info['version_number']
        )
        obj.ParameterBlock.component_path.Value = self.asset_info['component_path']
        obj.ParameterBlock.component_name.Value = self.asset_info['component_name']
        obj.ParameterBlock.asset_type.Value = self.asset_info['asset_type']
        obj.ParameterBlock.component_id.Value = self.asset_info['component_id']

        try:
            cmd = 'freeze ${0}'.format(self.node.Name)
            max_utils.eval_max_script(cmd)
        except:
            self.logger.debug(
                "Could not freeze object {0}".format(self.node.Name))
        return self.node

    def _get_asset_id_from_helper_node(self, helper_node):
        '''
        Find the asset version id added on the given *helperNode*. Then gets
        the asset version object from ftrack and Return the asset id of this
        asset version
        '''
        asset_version_id = helper_node.Object.ParameterBlock.asset_version_id.Value
        asset_version = ftrack.AssetVersion(id=asset_version_id)
        return asset_version.getAsset().getId()

    def _cleanup_selection_and_group_under_ftrack_node(self):
        '''
        Removes pre existing asset helper objects and parent the selected nodes
        to the current ftrack node.
        '''
        asset_id = self.asset_info['version_id']
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