# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

from ftrack_connect_pipeline.asset import FtrackAssetInfo, FtrackAssetBase
from ftrack_connect_pipeline_nuke.constants import asset as asset_const
from ftrack_connect_pipeline_nuke.utils import custom_commands as nuke_utils

import nuke


class FtrackAssetTab(FtrackAssetBase):
    '''
    Base FtrackAssetTab class.
    '''

    @property
    def loaded(self):
        '''
        Returns If the asset is loaded
        '''
        return self.asset_info[asset_const.IS_LOADED]

    @loaded.setter
    def loaded(self, value):
        '''
        Set the self :obj:`asset_info` as loaded and update the attributes in
        the current self :obj:`ftrack_object` if exists.

        *loaded* True if the objects are loaded in the scene.
        '''
        self.asset_info[asset_const.IS_LOADED] = value
        if self.ftrack_object:
            # Update and sync the ftrack_object asset_info with the
            # self.asset_info
            ftrack_node = nuke.toNode(self.ftrack_object)
            ftrack_node.knob(asset_const.IS_LOADED).setValue(
                str(self.asset_info[asset_const.IS_LOADED])
            )

    def __init__(self, event_manager):
        '''
        Initialize FtrackAssetTab with *event_manager*.

        *event_manager* instance of
        :class:`ftrack_connect_pipeline.event.EventManager`
        '''
        super(FtrackAssetTab, self).__init__(event_manager)
        self.connected_objects = []

    def init_ftrack_object(
        self,
        create_object=True,
    ):
        '''
        Returns the self :obj:`ftrack_object`.
        if the given *create_object* argument is set to True, creates a new
        :obj:`ftrack_object` with the self :obj:`asset_info` options on it.
        Otherwise, if the given *create_object* is set to False a matching
        :obj:`ftrack_object` will be found on the current scene based on the
        self :obj:`asset_info`.

        *create_object* If true creates a new ftrack object
        *is_loaded* Means that the objects are loaded in the scene, If true
        tags :obj:`asset_info` as loaded.
        '''
        ftrack_object = (
            self.create_new_ftrack_object()
            if create_object
            else self.get_ftrack_object_from_script()
        )

        if not ftrack_object:
            return None

        if not self.is_sync(ftrack_object):
            ftrack_object = self._update_ftrack_object(ftrack_object)

        self.ftrack_object = ftrack_object

        return self.ftrack_object

    def is_sync(self, ftrack_object):
        '''
        Returns bool if the current :obj:`asset_info` of the given
        *ftrack_object* is sync with the self :obj:`asset_info`
        '''
        return self._check_ftrack_object_sync(ftrack_object)

    @staticmethod
    def get_dictionary_from_ftrack_object(nuke_ftrack_obj_node):
        '''
        Static method to be used without initializing the current class.
        Returns a dictionary with the keys and values of the given
        *nuke_ftrack_obj_node* if exists.

        *nuke_ftrack_obj_node* FtrackAssetTab node type from nuke scene.
        '''
        param_dict = {}
        for knob in nuke_ftrack_obj_node.allKnobs():
            if knob.name() in asset_const.KEYS:
                if knob.name() == asset_const.DEPENDENCY_IDS:
                    param_dict[knob.name()] = []
                    for dep_id in (knob.getValue() or '').split(','):
                        if len(dep_id) > 0:
                            param_dict[knob.name()].append(dep_id)
                else:
                    param_dict[knob.name()] = knob.getValue()
        return param_dict

    def get_ftrack_object_from_script(self):
        '''
        Checks nuke scene to get all the FtrackAssetTab objects. Compares them
        with the current self :obj:`asset_info` and returns it if the asset_info_id
        matches.
        '''
        result_object = None
        for scene_node in nuke.root().nodes():
            if scene_node.knob(asset_const.FTRACK_PLUGIN_TYPE):
                param_dict = self.get_dictionary_from_ftrack_object(scene_node)
                # avoid read and write nodes containing the old ftrack tab
                # without information
                if not param_dict:
                    continue
                node_asset_info = FtrackAssetInfo(param_dict)
                if (
                    node_asset_info[asset_const.ASSET_INFO_ID]
                    == self.asset_info[asset_const.ASSET_INFO_ID]
                ):
                    self.logger.debug(
                        'Found existing node: {}'.format(scene_node)
                    )
                    result_object = scene_node.knob('name').value()

        return result_object

    def _check_ftrack_object_sync(self, ftrack_object):
        '''
        Check if the parameters of the given *ftrack_object* match the
        values of the current self :obj:`asset_info`.
        '''
        if not ftrack_object:
            self.logger.warning("ftrack tab doesn't exists")
            return False

        ftrack_node = nuke.toNode(ftrack_object)
        if not ftrack_node:
            self.logger.warning(
                "ftrack node {} doesn't exists".format(ftrack_object)
            )
            return False

        synced = False

        param_dict = self.get_dictionary_from_ftrack_object(ftrack_node)
        node_asset_info = FtrackAssetInfo(param_dict)

        if node_asset_info == self.asset_info:
            self.logger.debug("{} is synced".format(ftrack_node))
            synced = True

        return synced

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

    def connect_objects(self, objects):
        '''
        Link the given *objects* under current ftrack_object BackdropNode

        *objects* is List type of INode
        '''

        # TODO: find the way to get the screenWidth() now it's 0 don't know why,
        #  in nuke script editor returns the correct value. Also Find a way to
        #  ensure that there are no elements in the backdrop that shouldn't be
        #  there.
        self.connected_objects = []
        ftrack_node = nuke.toNode(self.ftrack_object)
        if ftrack_node.Class() != 'BackdropNode':
            return
        nuke_utils.cleanSelection()
        for node in objects:
            node['selected'].setValue(True)
            self.logger.debug("connecting node: {}".format(node.Class()))
            self.connected_objects.append(node.knob('name').value())

        ftrack_node.knob(asset_const.ASSET_LINK).setValue(
            ';'.join(self.connected_objects)
        )
        selected_nodes = nuke.selectedNodes()

        # TODO: move unwanted nodes out from the backdrop node
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

        return self.ftrack_object

    def _generate_ftrack_object_name(self):
        '''
        Return a scene name for the current self :obj:`ftrack_object`.
        '''

        ftrack_object_name = super(
            FtrackAssetTab, self
        )._generate_ftrack_object_name()

        if nuke.toNode(ftrack_object_name) is not None:
            error_message = "{} already exists in the scene".format(
                ftrack_object_name
            )
            self.logger.error(error_message)
            raise RuntimeError(error_message)
        # TODO: Test this before removing the code.
        # suffix = 0
        # while True:
        #     ftrack_object_name = '{}{}'.format(
        #         ftrack_object_name_base,
        #         ('_{}'.format(suffix)) if suffix > 0 else '',
        #     )
        #     if nuke.toNode(ftrack_object_name) is None:
        #         break
        #     suffix += 1
        return ftrack_object_name

    def create_new_ftrack_object(self):
        '''
        Creates a ftrack_object with a unique name.
        '''

        z_order = 0
        ftrack_node = nuke.nodes.BackdropNode(
            z_order=z_order, name=self._generate_ftrack_object_name()
        )

        ftrack_node.knob('tile_color').setValue(2386071295)
        self.ftrack_object = ftrack_node.knob('name').value()

        _tab = nuke.Tab_Knob(asset_const.FTRACK_PLUGIN_TYPE, 'ftrack')

        if 'published' in ftrack_node.knobs():
            if ftrack_node.published():
                ftrack_node["published"].fromScript("0")

        ftrack_node.addKnob(_tab)

        for k in list(self.asset_info.keys()):
            knob = nuke.String_Knob(k)
            ftrack_node.addKnob(knob)

        knob = nuke.String_Knob(asset_const.ASSET_LINK)
        ftrack_node.addKnob(knob)

        self._set_scene_node_color(ftrack_node)

        return self.ftrack_object

    def _update_ftrack_object(self, ftrack_object):
        '''
        Updates the parameters of the given *ftrack_object* based on the
        self :obj:`asset_info`.
        '''

        ftrack_node = nuke.toNode(ftrack_object)
        if not ftrack_node:
            raise Exception(
                'ftrack node "{}" doesnt exists'.format(ftrack_object)
            )
        for k, v in self.asset_info.items():
            if k == asset_const.REFERENCE_OBJECT:
                ftrack_node.knob(k).setValue(str(ftrack_node.Class()))
            elif k == asset_const.DEPENDENCY_IDS:
                ftrack_node.knob(k).setValue(','.join(v or []))
            else:
                ftrack_node.knob(k).setValue(str(v))
        if 'published' in ftrack_node.knobs():
            ftrack_node.reload()

        return ftrack_node.knob('name').value()

    def _set_scene_node_color(self, ftrack_node, latest=True):
        '''
        Sets the visual color of the ftrack_object
        '''
        # Green RGB 20, 161, 74
        # Orange RGB 227, 99, 22
        latest_color = int('%02x%02x%02x%02x' % (20, 161, 74, 255), 16)
        old_color = int('%02x%02x%02x%02x' % (227, 99, 22, 255), 16)
        if latest:
            ftrack_node.knob("note_font_color").setValue(latest_color)
        else:
            ftrack_node.knob("note_font_color").setValue(old_color)
