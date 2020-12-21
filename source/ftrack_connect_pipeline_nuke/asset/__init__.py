# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

import json
import ftrack_api
from ftrack_connect_pipeline.asset import FtrackAssetInfo, FtrackAssetBase
from ftrack_connect_pipeline_nuke.constants import asset as asset_const
from ftrack_connect_pipeline import constants as core_const
from ftrack_connect_pipeline_nuke.utils import custom_commands as nuke_utils
from ftrack_connect_pipeline_nuke.constants.asset import modes as load_const

import nuke


class FtrackAssetTab(FtrackAssetBase):
    '''
    Base FtrackAssetTab class.
    '''

    def is_sync(self, ftrack_object):
        '''Returns bool if the current ftrack_object is sync'''
        return self._check_ftrack_object_sync(ftrack_object)

    def __init__(self, event_manager):
        '''
        Initialize FtrackAssetTab with *event_manager*.

        *event_manager* instance of
        :class:`ftrack_connect_pipeline.event.EventManager`
        '''
        super(FtrackAssetTab, self).__init__(event_manager)
        self.connected_objects = []

    def init_ftrack_object(self):
        '''
        Return the ftrack ftrack_object for this class. It checks if there is
        already a matching ftrack ftrack_object in the scene, in this case it
        updates the ftrack_object if it's not. In case there is no ftrack_object
        in the scene this function creates a new one.
        '''
        ftrack_object = self.get_ftrack_object_from_nuke()
        if not ftrack_object:
            ftrack_object = self.create_new_ftrack_object()
        if ftrack_object:
            if not self.is_sync(ftrack_object):
                ftrack_object = self._update_ftrack_object(ftrack_object)

        self.ftrack_object = ftrack_object

        return self.ftrack_object

    @staticmethod
    def get_parameters_dictionary(scene_node):
        '''
        Returns a diccionary with the keys and values of the given *scene_node*
        parameters
        '''
        param_dict = {}
        for knob in scene_node.allKnobs():
            if knob.name() in asset_const.KEYS:
                param_dict[knob.name()] = knob.getValue()
        return param_dict

    def get_ftrack_object_from_nuke(self):
        '''
        Return the ftrack_object from the current asset_version if it exists in
        the scene.
        '''
        for scene_node in nuke.root().nodes():
            if scene_node.knob(asset_const.FTRACK_PLUGIN_TYPE):
                param_dict = self.get_parameters_dictionary(scene_node)
                # avoid read and write nodes containing the old ftrack tab
                # without information
                if not param_dict:
                    continue
                node_asset_info = FtrackAssetInfo(param_dict)
                if node_asset_info.is_deprecated:
                    raise DeprecationWarning(
                        "Can not read v1 ftrack asset plugin")
                if (
                        node_asset_info[asset_const.REFERENCE_OBJECT] ==
                        self.asset_info[asset_const.REFERENCE_OBJECT]
                ):
                    return scene_node.knob('name').value()

    def _check_ftrack_object_sync(self, ftrack_object):
        '''
        Check if the current parameters of the ftrack_object match the
        values of the asset_info.
        '''
        if not ftrack_object:
            self.logger.warning("Ftrack tab doesn't exists")
            return False

        synced = False
        ftrack_object = nuke.toNode(ftrack_object)
        param_dict = self.get_parameters_dictionary(ftrack_object)
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
            FtrackAssetTab, self
        )._get_unique_ftrack_object_name()


        count = 0
        while 1:
            if nuke.exists(ftrack_object_name):
                ftrack_object_name = ftrack_object_name + str(count)
                count = count + 1
            else:
                break
        return ftrack_object_name

    def _node_is_inside(self, node, backdrop_node):
        '''
        Returns true if *node* geometry is inside *backdropNode* otherwise
        returns false
        '''

        top_left_node = [node.xpos(), node.ypos()]

        top_left_backdrop = [backdrop_node.xpos(), backdrop_node.ypos()]

        bottom_right_node = [node.xpos() + node.screenWidth(),
                           node.ypos() + node.screenHeight()]

        bottom_right_backdrop = [backdrop_node.xpos() + backdrop_node.screenWidth(),
                               backdrop_node.ypos() + backdrop_node.screenHeight()]

        top_left = (top_left_node[0] >= top_left_backdrop[0]) and (
                    top_left_node[1] >= top_left_backdrop[1])

        bottom_right = (bottom_right_node[0] <= bottom_right_backdrop[0]) and (
                    bottom_right_node[1] <= bottom_right_backdrop[1])

        return top_left and bottom_right

    def connect_objects(self, objects):
        '''
        Parent the given *objects* under current ftrack_object

        *objects* is List type of INode
        '''

        # TODO: find the way to get the screenWidth() now it's 0 don't know why,
        #  in nuke script editor returns the correct value. Also Find a way to
        #  ensure that there are no elements in the backdrop that shouldn't be
        #  there.
        self.connected_objects = []
        ftrack_object = nuke.toNode(self.ftrack_object)
        if ftrack_object.Class() != 'BackdropNode':
            return
        nuke_utils.cleanSelection()
        for node in objects:
            node['selected'].setValue(True)
            self.logger.info("connecting node: {}".format(node.Class()))
            self.connected_objects.append(node.knob('name').value())

        ftrack_object.knob(asset_const.ASSET_LINK).setValue(
            ';'.join(self.connected_objects)
        )
        selected_nodes = nuke.selectedNodes()

        #TODO: move unwanted nodes out from the backdrop node
        # all_nodes = nuke.allNodes()
        # scene_nodes = list(set(all_nodes) - set(selected_nodes))
        # scene_nodes.remove(ftrack_object)
        #
        # for node in scene_nodes:
        #     if self._node_is_inside(node, ftrack_object):
        #         new_pos = ftrack_object.xpos() + (
        #                 node.xpos() - ftrack_object.xpos()
        #         ) * 2
        #         node['xpos'].setValue(new_pos)

        # Calculate bounds for the backdrop node.
        bd_X = min([node.xpos() for node in selected_nodes])
        bd_Y = min([node.ypos() for node in selected_nodes])
        bd_W = max([node.xpos() + 80 for node in selected_nodes]) - bd_X
        bd_H = max([node.ypos() + 20 for node in selected_nodes]) - bd_Y

        z_order = 0
        selected_backdrop_nodes = nuke.selectedNodes("BackdropNode")
        # if there are backdropNodes selected put the new one immediately behind
        # the farthest one
        if len(selected_backdrop_nodes):
            z_order = min(
                [node.knob("z_order").value() for node in selected_backdrop_nodes]
            ) - 1
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
        left, top, right, bottom = (-10, -80, 10, 10)
        bd_X += left
        bd_Y += top
        bd_W += (right - left)
        bd_H += (bottom - top)

        ftrack_object['xpos'].setValue(bd_X)
        ftrack_object['bdwidth'].setValue(bd_W)
        ftrack_object['ypos'].setValue(bd_Y)
        ftrack_object['bdheight'].setValue(bd_H)
        ftrack_object['z_order'].setValue(z_order)

        if ftrack_object.getNodes() != selected_nodes:
            self.logger.info("There are nodes that shouldn't be on the backdrop")
            self.logger.info("in backdrop node: {}".format(
                ftrack_object.getNodes())
            )
            self.logger.info("in selected nodes: {}".format(selected_nodes))

        return self.ftrack_object

    def create_new_ftrack_object(self):
        '''
        Creates a ftrack_object with a unique name.
        '''

        if not self.ftrack_object:
            z_order = 0
            ftrack_object = nuke.nodes.BackdropNode(z_order=z_order)
            ftrack_object.knob('tile_color').setValue(2386071295)
            self.ftrack_object = ftrack_object.knob('name').value()

        ftrack_object = nuke.toNode(self.ftrack_object)

        if (
                self.asset_info[asset_const.LOAD_MODE] == load_const.IMPORT_MODE
                or
                self.asset_info[asset_const.LOAD_MODE] == load_const.REFERENCE_MODE
        ):
            ftrack_object.knob('name').setValue(
                self._get_unique_ftrack_object_name()
            )
            self.ftrack_object = ftrack_object.knob('name').value()

        _tab = nuke.Tab_Knob(asset_const.FTRACK_PLUGIN_TYPE, 'ftrack')

        if 'published' in ftrack_object.knobs():
            if ftrack_object.published():
                ftrack_object["published"].fromScript("0")

        ftrack_object.addKnob(_tab)

        for k in list(self.asset_info.keys()):
            knob = nuke.String_Knob(k)
            ftrack_object.addKnob(knob)

        knob = nuke.String_Knob(asset_const.ASSET_LINK)
        ftrack_object.addKnob(knob)

        self._set_scene_node_color(ftrack_object.knob('name').value())

        return ftrack_object.knob('name').value()

    def _update_ftrack_object(self, ftrack_object):
        '''
        Update the parameters of the ftrack_object. And Return the
        ftrack_object updated
        '''

        ftrack_object = nuke.toNode(ftrack_object)

        for k, v in self.asset_info.items():
            ftrack_object.knob(k).setValue(str(v))
            if k == asset_const.REFERENCE_OBJECT:
                ftrack_object.knob(k).setValue(str(ftrack_object.Class()))

        if 'published' in ftrack_object.knobs():
            ftrack_object.reload()

        return ftrack_object.knob('name').value()

    def _set_scene_node_color(self, ftrack_object, latest=True):
        '''
        Sets the visual color of the ftrack_object
        '''
        # Green RGB 20, 161, 74
        # Orange RGB 227, 99, 22
        ftrack_object = nuke.toNode(ftrack_object)
        latest_color = int('%02x%02x%02x%02x' % (20, 161, 74, 255), 16)
        old_color = int('%02x%02x%02x%02x' % (227, 99, 22, 255), 16)
        if latest:
            ftrack_object.knob("note_font_color").setValue(latest_color)
        else:
            ftrack_object.knob("note_font_color").setValue(old_color)
