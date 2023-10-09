# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import logging
from ftrack_framework_core.asset.dcc_object import DccObject
from ftrack_framework_nuke.constants import asset as asset_const
from ftrack_framework_nuke import utils as nuke_utils

import nuke


class NukeDccObject(DccObject):
    '''NukeDccObject class.'''

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
        super(NukeDccObject, self).__init__(name, from_id, **kwargs)

    def __setitem__(self, k, v):
        '''
        Sets the given *v* into the given *k* and automatically set the
        attributes of the current self :obj:`name` on the DCC
        '''
        ftrack_node = nuke.toNode(self.name)
        if not ftrack_node:
            raise Exception(
                'ftrack node "{}" does not exists'.format(self.name)
            )
        if k == asset_const.REFERENCE_OBJECT:
            ftrack_node.knob(k).setValue(str(ftrack_node.Class()))
        elif k == asset_const.DEPENDENCY_IDS:
            ftrack_node.knob(k).setValue(','.join(v or []))
        else:
            ftrack_node.knob(k).setValue(str(v))

        if 'published' in ftrack_node.knobs():
            ftrack_node.reload()

        super(NukeDccObject, self).__setitem__(k, v)

    def create(self, name):
        '''
        Creates a new dcc_object with the given *name* if doesn't exists.
        '''
        if self._name_exists(name):
            error_message = "{} already exists in the scene".format(name)
            self.logger.error(error_message)
            raise RuntimeError(error_message)

        z_order = 0
        ftrack_node = nuke.nodes.BackdropNode(z_order=z_order, name=name)

        ftrack_node.knob('tile_color').setValue(self.ftrack_plugin_id)
        self.name = ftrack_node.knob('name').value()

        _tab = nuke.Tab_Knob(asset_const.FTRACK_PLUGIN_TYPE, 'ftrack')

        if 'published' in ftrack_node.knobs():
            if ftrack_node.published():
                ftrack_node["published"].fromScript("0")

        ftrack_node.addKnob(_tab)

        for k in asset_const.KEYS:
            knob = nuke.String_Knob(k)
            ftrack_node.addKnob(knob)

        knob = nuke.String_Knob(asset_const.ASSET_LINK)
        ftrack_node.addKnob(knob)

        self._set_scene_node_color(ftrack_node)

        return self.name

    def _name_exists(self, name):
        '''
        Return true if the given *name* exists in the scene.
        '''
        if nuke.toNode(name):
            return True

        return False

    def from_asset_info_id(self, asset_info_id):
        '''
        Checks nuke scene to get all the ftrackAssetNode objects. Compares them
        with the given *asset_info_id* and returns them if matches.
        '''
        for scene_node in nuke.root().nodes():
            if scene_node.knob(asset_const.FTRACK_PLUGIN_TYPE):
                id_value = scene_node.knob(
                    asset_const.ASSET_INFO_ID
                ).getValue()

                if id_value == asset_info_id:
                    self.logger.debug(
                        'Found existing object: {}'.format(
                            scene_node.knob('name').value()
                        )
                    )
                    self.name = scene_node.knob('name').value()
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

        *object_name* ftrackAssetNode object type from nuke scene.
        '''
        logger = logging.getLogger(
            '{0}.{1}'.format(__name__, __class__.__name__)
        )
        param_dict = {}
        obj_node = nuke.toNode(object_name)
        if not obj_node:
            error_message = "{} Object doesn't exists".format(object_name)
            logger.error(error_message)
            return param_dict

        for knob in obj_node.allKnobs():
            if knob.name() in asset_const.KEYS:
                if knob.name() == asset_const.DEPENDENCY_IDS:
                    param_dict[knob.name()] = []
                    for dep_id in (knob.getValue() or '').split(','):
                        if len(dep_id) > 0:
                            param_dict[knob.name()].append(dep_id)
                elif knob.name() in [
                    asset_const.OBJECTS_LOADED,
                    asset_const.IS_LATEST_VERSION,
                ]:
                    param_dict[knob.name()] = (
                        knob.getValue() or ''
                    ).lower() in ['true', '1']
                else:
                    param_dict[knob.name()] = knob.getValue()

        return param_dict

    def connect_objects(self, objects):
        '''
        Link the given *objects* ftrack attribute to the self
        :obj:`name` object asset_link attribute in Nuke.

        *objects* List of Nuke objects
        '''
        connected_objects = []
        ftrack_node = nuke.toNode(self.name)
        if ftrack_node.Class() != 'BackdropNode':
            return
        nuke_utils.clean_selection()
        for node in objects:
            if node == ftrack_node:
                continue
            node['selected'].setValue(True)
            self.logger.debug("connecting node: {}".format(node.Class()))
            connected_objects.append(node.knob('name').value())

        ftrack_node.knob(asset_const.ASSET_LINK).setValue(
            ';'.join(connected_objects)
        )
        selected_nodes = nuke.selectedNodes()

        # Calculate bounds for the backdrop node.
        bd_X = min([node.xpos() for node in selected_nodes])
        bd_Y = min([node.ypos() for node in selected_nodes])
        bd_W = max([node.xpos() + 80 for node in selected_nodes]) - bd_X
        bd_H = max([node.ypos() + 80 for node in selected_nodes]) - bd_Y

        z_order = 0
        selected_backdrop_nodes = nuke.selectedNodes("BackdropNode")
        # if there are backdropNodes selected put the new one immediately behind
        # the farthest one
        if len(selected_backdrop_nodes):
            z_order = (
                min(
                    [
                        node.knob("z_order").value()
                        for node in selected_backdrop_nodes
                    ]
                )
                - 1
            )
        else:
            # otherwise (no backdrop in selection) find the nearest backdrop if
            # exists and set the new one in front of it
            non_selected_backdrop_nodes = nuke.allNodes("BackdropNode")
            for non_backdrop in selected_nodes:
                for backdrop in non_selected_backdrop_nodes:
                    if self._node_is_inside(non_backdrop, backdrop):
                        z_order = max(
                            z_order, backdrop.knob("z_order").value() + 1
                        )
        # Expand the bounds to leave a little border. Elements are offsets for
        # left, top, right and bottom edges respectively
        left, top, right, bottom = (-10, -20, 10, 10)
        bd_X += left
        bd_Y += top
        bd_W += right - left
        bd_H += bottom - top

        ftrack_node.setXpos(bd_X)
        ftrack_node.setYpos(bd_Y)
        ftrack_node['bdwidth'].setValue(bd_W)
        ftrack_node['bdheight'].setValue(bd_H)
        ftrack_node['z_order'].setValue(z_order)

        if ftrack_node.getNodes() != selected_nodes:
            self.logger.warning(
                "There are nodes that shouldn't be on the backdrop"
            )
            self.logger.warning(
                "in backdrop node: {}".format(ftrack_node.getNodes())
            )
            self.logger.warning("in selected nodes: {}".format(selected_nodes))

    def _set_scene_node_color(self, latest=True):
        '''
        Sets the visual color of the dcc_object
        '''
        # Green RGB 20, 161, 74
        # Orange RGB 227, 99, 22
        ftrack_node = nuke.toNode(self.name)
        latest_color = int('%02x%02x%02x%02x' % (20, 161, 74, 255), 16)
        old_color = int('%02x%02x%02x%02x' % (227, 99, 22, 255), 16)
        if latest:
            ftrack_node.knob("note_font_color").setValue(latest_color)
        else:
            ftrack_node.knob("note_font_color").setValue(old_color)

    def _node_is_inside(self, node, backdrop_node):
        '''
        Returns true if *node* geometry is inside *backdropNode* otherwise
        returns false
        '''

        top_left_node = [node.xpos(), node.ypos()]

        top_left_backdrop = [backdrop_node.xpos(), backdrop_node.ypos()]

        bottom_right_node = [
            node.xpos() + node.screenWidth(),
            node.ypos() + node.screenHeight(),
        ]

        bottom_right_backdrop = [
            backdrop_node.xpos() + backdrop_node.screenWidth(),
            backdrop_node.ypos() + backdrop_node.screenHeight(),
        ]

        top_left = (top_left_node[0] >= top_left_backdrop[0]) and (
            top_left_node[1] >= top_left_backdrop[1]
        )

        bottom_right = (bottom_right_node[0] <= bottom_right_backdrop[0]) and (
            bottom_right_node[1] <= bottom_right_backdrop[1]
        )

        return top_left and bottom_right
