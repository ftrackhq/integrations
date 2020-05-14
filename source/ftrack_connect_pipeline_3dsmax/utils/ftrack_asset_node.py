import ftrack

import MaxPlus

from ftrack_connect_pipeline import asset
from ftrack_connect_pipeline_3dsmax.constants.asset import v1, v2
from ftrack_connect_pipeline_3dsmax import constants
import custom_commands as max_utils

import logging

def is_ftrack_asset_helper(node):
    '''Return True if the node is a Ftrack asset helper node.'''
    if node.Object.ClassID == MaxPlus.Class_ID(
            constants.FTRACK_ASSET_CLASS_ID[0], constants.FTRACK_ASSET_CLASS_ID[1]
    ):
        return True

    return False


class FtrackAssetInfoV1Max(asset.FtrackAssetInfoV1):
    def __init__(self, context, data, session, options):
        super(FtrackAssetInfoV1Max, self).__init__(context, data, session)
        self[v1.ASSET_LOAD_MODE] = options.get('asset_load_mode', '')
        self[v1.ALEMBIC_IMPORT_ARGS] = options.get('alembic_import_args', '')


class FtrackAssetInfoV2Max(asset.FtrackAssetInfoV2):
    def __init__(self, context, data, session, options):
        super(FtrackAssetInfoV2Max, self).__init__(context, data, session)
        self[v2.ASSET_LOAD_MODE] = options.get('asset_load_mode', '')
        self[v2.ALEMBIC_IMPORT_ARGS] = options.get('alembic_import_args', '')

class FtrackAssetInfoMax(asset.FtrackAssetInfo):
    '''
    Dictionary class containing ftrack asset information from the given context
    '''
    def __init__(self, context, data, session):
        '''
        Initialize FtrackAssetInfo with the give *context*, *data* and *session*.

        *context* Dicctionary with asset_name, asset_type, asset_id,
        version_number, version_id, context_id keys and values from the current
        asset.
        *data* List of component paths of the current asset.
        *session* should be the :class:`ftrack_api.session.Session` instance
        to use for communication with the server.
        '''
        super(FtrackAssetInfoMax, self).__init__()
        self.update(FtrackAssetInfoV1(context, data, session))
        self.update(FtrackAssetInfoV2(context, data, session))


class FtrackAssetNode(asset.FtrackAssetBase):
    '''
        Base FtrackAssetNode class.
    '''
    def __init__(self, context, data, options, session):
        '''
            Initialize FtrackAssetNode with *asset_info*, and optional
            *asset_import_mode*.

            *asset_info* Dictionary with the current asset information from
            ftrack. Needed keys: asset_name, version_number, context_id,
            asset_type, asset_id, version_id, component_name, component_id,
            compoennt_path.
        '''
        super(FtrackAssetNode, self).__init__(context, data, session)

        self.nodes = []
        self.node = None

        self.options = options

        self.helper_object = MaxPlus.Factory.CreateHelperObject(
            MaxPlus.Class_ID(
                constants.FTRACK_ASSET_CLASS_ID[0],
                constants.FTRACK_ASSET_CLASS_ID[1]
            )
        )
        self.logger.debug(
            'helper_object {} has been created'.format(self.helper_object)
        )

    def load_asset_info(self):

    def add_value_to_asset_info(self, key, value):
        self.asset_info['asset_load_mode'] = options.get('asset_load_mode', '')
        self.asset_info['alembic_import_args'] = options.get('alembic_import_args', '')

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
            if not self.check_ftrack_node_sync():
                self._update_ftrack_asset_node()

        else:
            self.create_new_node()

        return self.node

    def _check_is_legacy_node(self, ftrack_node):
        '''
        Return if the given *ftrack_node* is from the legacy framework
        '''
        obj = ftrack_node.Object

        if 'version_id' in obj.ParameterBlock.Parameters:
            if (
                    obj.ParameterBlock.version_id.Value ==
                    obj.ParameterBlock.Parameters.assetId.Value
            ):
                return False
        return True

    def get_ftrack_node_from_scene(self):
        '''
        Return the ftrack node of the current asset_version of the scene if
        exists.
        '''
        ftrack_asset_nodes = max_utils.get_ftrack_helpers()
        for ftrack_node in ftrack_asset_nodes:
            obj = ftrack_node.Object
            if self._check_is_legacy_node(ftrack_node):
                version_id = obj.ParameterBlock.asset_id.Value
                if (
                        version_id == self.asset_info['version_id']
                ):
                    return ftrack_node
            else:
                version_id = obj.ParameterBlock.version_id.Value
                asset_id = obj.ParameterBlock.asset_id.Value
                if (
                        version_id == self.asset_info['version_id'] and
                        asset_id == self.asset_info['asset_id']
                ):
                    return ftrack_node

    def set_ftrack_node(self, ftrack_node):
        '''
        Sets the given *ftrack_node* as the current self.node of the class
        '''
        self.node = ftrack_node

    def check_ftrack_node_sync(self):
        '''
        Check if the current parameters of the ftrack node match the parameters
        of the porperty asset_info.

        ..Note:: Checks only the new parameters not the legacy ones

        '''
        if not self.node:
            self.logger.warning("No ftrack node loaded")
            return None

        synced = False
        obj = self.node.Object
        for p in obj.ParameterBlock.Parameters:
            if p.Name in constants.LEGACY_PARAMETERS_MAPPING.keys():
                new_key = constants.LEGACY_PARAMETERS_MAPPING[p.Name]
                if p.Value != self.asset_info[new_key]:
                    self.logger.debug("{} is not synced".format(self.node))
                    return False
                else:
                    synced = True
            elif p.Name in self.asset_info.keys():
                if p.Value != self.asset_info[p.Name]:
                    self.logger.debug("{} is not synced".format(self.node))
                    return False
                else:
                    synced = True
        return synced

    def _get_unique_ftrack_node_name(self, asset_name):
        '''
        Return a unique scene name for the given *asset_name*
        '''
        return max_utils.get_unique_node_name('{}_ftrackdata'.format(asset_name))

    def connect_objects_to_ftrack_node(self, objects):
        '''
        Parent the given *objects* under current ftrack_node

        *objects* is List type of INode
        '''

        max_utils.deselect_all()
        for obj in objects:
            max_utils.add_node_to_selection(obj)
        self._connect_selection()
        if self.asset_info['asset_load_mode'] != constants.SCENE_XREF_MODE:
            self.reload_references_from_selection()

    def get_load_mode_from_node(self, node):
        '''Return the import mode used to import an asset.'''
        obj = node.Object
        return obj.ParameterBlock.asset_load_mode.Value

    def reload_references_from_selection(self):
        '''
        Reload all the ftrack dependencies that are referenced in the current
        selection.
        '''
        for node in MaxPlus.SelectionManager.Nodes:
            if is_ftrack_asset_helper(node) and self.get_load_mode_from_node(
                    node) == constants.SCENE_XREF_MODE:
                if not max_utils.scene_XRef_imported(node):
                    self.logger.debug(u'Re-importing {0} scene xref.'.format(
                        node.Name))
                    max_utils.re_import_scene_XRef(
                        node.Object.ParameterBlock.component_path.Value,
                        node.Name
                    )

    def create_new_node(self):
        '''
        Creates the ftrack_node with a unique name. The ftrack node is type of
        FtrackAssetHelper.

        '''
        name = self._get_unique_ftrack_node_name(
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
        except Exception, e:
            self.logger.debug(
                "Could not freeze object {0}, Error: {1}".format(
                    self.asset_info['asset_name'], e
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

        for p in obj.ParameterBlock.Parameters:
            if p.Name in constants.LEGACY_PARAMETERS_MAPPING.keys():
                new_key = constants.LEGACY_PARAMETERS_MAPPING[p.Name]
                p.SetValue(self.asset_info[new_key])
            elif p.Name in self.asset_info.keys():
                p.SetValue(self.asset_info[p.Name])

        try:
            cmd = 'freeze ${0}'.format(self.node.Name)
            max_utils.eval_max_script(cmd)
        except Exception, e:
            self.logger.debug(
                "Could not freeze object {0}, Error: {1}".format(
                    self.node.Name, e
                )
            )
        return self.node

    def _get_asset_id_from_helper_node(self, helper_node):
        '''
        Find the asset version id added on the given *helperNode*. Then gets
        the asset version object from ftrack and Return the asset id of this
        asset version
        '''
        version_id = helper_node.Object.ParameterBlock.version_id.Value
        asset_version = ftrack.AssetVersion(id=version_id)
        return asset_version.getAsset().getId()

    def _connect_selection(self):
        '''
        Removes pre existing asset helper objects and parent the selected nodes
        to the current ftrack node.
        '''
        version_id = self.asset_info['version_id']
        root_node = MaxPlus.Core.GetRootNode()

        nodes_to_delete = []

        self.logger.debug(u'Removing duplicated asset helper objects')
        for node in MaxPlus.SelectionManager.Nodes:
            if is_ftrack_asset_helper(node) and node.Parent == root_node:
                helper_version_id = self._get_asset_id_from_helper_node(node)
                if helper_version_id == version_id:
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
                self.logger.debug(
                    'node {} added to ftrack node {}'.format(node, self.node)
                )
