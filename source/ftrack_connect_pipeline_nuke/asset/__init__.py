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
    Base FtrackAssetNode class.
    '''

    def is_sync(self):
        return self._check_ftrack_object_sync()

    def __init__(self, event_manager):
        '''
        Initialize FtrackAssetTab with *ftrack_asset_info*, and *session*.

        *ftrack_asset_info* should be the
        :class:`ftrack_connect_pipeline.asset.asset_info.FtrackAssetInfo`
        instance.
        *session* should be the :class:`ftrack_api.session.Session` instance
        to use for communication with the server.
        '''
        super(FtrackAssetTab, self).__init__(event_manager)
        self.connected_objects = []

    def init_ftrack_object(self):
        '''
        Return the scene ftrack_object for this class. It checks if there is already a
        matching ftrack tab in the scene, and the tab if needed. In case there
        is no ftrack tab in the scene this function creates a new one on the
        given *scene_node*.
        '''
        self.logger.info("comming from init_ftrack_object")
        ftrack_object = self.get_ftrack_object_from_nuke()
        if ftrack_object:
            self.logger.info("yes we have a ftrack_object from the scene")
            self._set_ftrack_object(ftrack_object)
            if not self.is_sync():
                self._update_ftrack_object()
        else:
            self.logger.info("no we don't have a ftrack_object from the scene")
            self.create_new_ftrack_object()

        # TODO: Shouldn't return the ftrack_object???
        return self.ftrack_object

    def set_ftrack_object(self, ftrack_object=None):
        self.logger.info("comming from set_ftrack_object")
        scene_ftrack_object = self.get_ftrack_object_from_nuke()
        if scene_ftrack_object:
            self._set_ftrack_object(scene_ftrack_object)
            return scene_ftrack_object
        if ftrack_object:
            ftrack_object = nuke.toNode(ftrack_object)
            self._set_ftrack_object(ftrack_object)
            return ftrack_object

        ftrack_object = nuke.nodes.BackdropNode()
        ftrack_object.knob('tile_color').setValue(2386071295)
        self.logger.info("setting the new ftrack_object")
        self._set_ftrack_object(ftrack_object)
        return ftrack_object

    def _get_parameters_dictionary(self, scene_node):
        '''
        Returns a dicctionary with the matching keys and values of the asset info
        if the current scene_node have the ftrack tab.
        '''
        param_dict = {}
        for knob in scene_node.allKnobs():
            if knob.name() in asset_const.KEYS:
                param_dict[knob.name()] = knob.getValue()
        return param_dict

    def get_ftrack_object_from_nuke(self):
        '''
        Return the ftrack tab knob of the current scene ftrack_object in case the tab
        exists and the values match the asset info values.
        '''
        for scene_node in nuke.root().nodes():
            if scene_node.knob(asset_const.FTRACK_PLUGIN_TYPE):
                param_dict = self._get_parameters_dictionary(scene_node)
                node_asset_info = FtrackAssetInfo(param_dict)
                self.logger.info(
                    "self.asset_info --> {}".format(
                        self.asset_info
                    )
                )
                self.logger.info(
                    "self.asset_info[asset_const.REFERENCE_OBJECT] --> {}".format(
                        self.asset_info[asset_const.REFERENCE_OBJECT]
                    )
                )
                self.logger.info(
                    "asset_info[asset_const.REFERENCE_OBJECT] --> {}".format(
                        node_asset_info[asset_const.REFERENCE_OBJECT]
                    )
                )
                if node_asset_info.is_deprecated:
                    raise DeprecationWarning(
                        "Can not read v1 ftrack asset plugin")
                if (
                        node_asset_info[asset_const.REFERENCE_OBJECT] ==
                        self.asset_info[asset_const.REFERENCE_OBJECT]
                ):
                    return scene_node

    def _check_ftrack_object_sync(self):
        '''
        Check if the current parameters of the ftrack tab match the values
        of the asset_info.
        '''
        if not self.ftrack_object:
            self.logger.warning("Ftrack tab doesn't exists")
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
            if nuke.exists(ftrack_object_name):
                ftrack_object_name = ftrack_object_name + str(count)
                count = count + 1
            else:
                break
        return ftrack_object_name

    def _node_is_inside(self, node, backdrop_node):
        """Returns true if node geometry is inside backdropNode otherwise returns false"""

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
        if self.ftrack_object.Class() != 'BackdropNode':
            return
        nuke_utils.cleanSelection()
        for node in objects:
            node['selected'].setValue(True)
            self.logger.info("connecting node: {}".format(node.Class()))
            self.connected_objects.append(node.knob('name').value())
        # TODO:if this fail just add the classes instead of the full node.
        self.ftrack_object.knob(asset_const.ASSET_LINK).setValue(
            ';'.join(self.connected_objects)
        )
        selected_nodes = nuke.selectedNodes()
        # Calculate bounds for the backdrop node.
        bd_X = min([node.xpos() for node in selected_nodes])
        bd_Y = min([node.ypos() for node in selected_nodes])
        bd_W = max([node.xpos() + 80 for node in selected_nodes]) - bd_X
        bd_H = max([node.ypos() + 20 for node in selected_nodes]) - bd_Y

        # bd_W = max(
        #     [node.xpos() + node.screenWidth() for node in selected_nodes]
        # ) - bd_X
        # bd_H = max(
        #     [node.ypos() + node.screenHeight() for node in selected_nodes]
        # ) - bd_Y

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

        self.ftrack_object['xpos'].setValue(bd_X)
        self.ftrack_object['bdwidth'].setValue(bd_W)
        self.ftrack_object['ypos'].setValue(bd_Y)
        self.ftrack_object['bdheight'].setValue(bd_H)

        if self.ftrack_object.getNodes() != selected_nodes:
            self.logger.info("There are nodes that shouldn't be on the backdrop")
            self.logger.info("in backdrop node: {}".format(
                self.ftrack_object.getNodes())
            )
            self.logger.info("in selected nodes: {}".format(selected_nodes))

        return self.ftrack_object

    def create_new_ftrack_object(self):
        '''
        Creates an ftrack tab to the current scene_node.
        '''

        if (
                self.asset_info[asset_const.LOAD_MODE] == load_const.IMPORT_MODE
                or
                self.asset_info[asset_const.LOAD_MODE] == load_const.REFERENCE_MODE
        ):
            self.ftrack_object.knob('name').setValue(
                self._get_unique_ftrack_object_name()
            )
        # TODO: no sure if this will work, also maybe it's better no name it on
        #  creation but we don't have acces to a unique name then

        _tab = nuke.Tab_Knob(asset_const.FTRACK_PLUGIN_TYPE, 'ftrack')

        if 'published' in self.ftrack_object.knobs():
            if self.ftrack_object.published():
                self.ftrack_object["published"].fromScript("0")

        self.ftrack_object.addKnob(_tab)

        for k in self.asset_info.keys():
            knob = nuke.String_Knob(k)
            self.ftrack_object.addKnob(knob)

        knob = nuke.String_Knob(asset_const.ASSET_LINK)
        self.ftrack_object.addKnob(knob)

        self._set_scene_node_color()

        self._ftrack_objects.append(self.ftrack_object)

        return self._update_ftrack_object()

    def _update_ftrack_object(self):
        '''
        Update the parameters of the ftrack tab. And Return the scene ftrack_object
        updated
        '''

        for k, v in self.asset_info.items():
            self.ftrack_object.knob(k).setValue(str(v))
            if k == asset_const.REFERENCE_OBJECT:
                self.ftrack_object.knob(k).setValue(str(self.ftrack_object))

        if 'published' in self.ftrack_object.knobs():
            self.ftrack_object.reload()

        return self.ftrack_object

    def _set_scene_node_color(self, latest=True):
        # Green RGB 20, 161, 74
        # Orange RGB 227, 99, 22
        latest_color = int('%02x%02x%02x%02x' % (20, 161, 74, 255), 16)
        old_color = int('%02x%02x%02x%02x' % (227, 99, 22, 255), 16)
        if latest:
            self.ftrack_object.knob("note_font_color").setValue(latest_color)
        else:
            self.ftrack_object.knob("note_font_color").setValue(old_color)

    def _change_version(self, event):
        '''
        Override function from the main class, remove the current assets of the
        scene and loads the given version of the asset in the *event*. Then
        super the base function.
        '''
        asset_info = event['data']
        # self.logger.debug("Change version from: {}".format(self.asset_info))
        # self.logger.debug("to: {}".format(asset_info))
        # self.logger.debug("current ref object: {}".format(
        #     self.asset_info[asset_const.REFERENCE_OBJECT]
        # ))
        # self.logger.debug("next ref object: {}".format(
        #     asset_info[asset_const.REFERENCE_OBJECT]
        # ))
        self.logger.debug("connected objects in _change_version: {}".format(
            self.connected_objects
        ))

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
        self.logger.debug("event['data'][asset_const.REFERENCE_OBJECT]: {}".format(
            event['data'][asset_const.REFERENCE_OBJECT]
        ))
        super(FtrackAssetTab, self)._change_version(event)

    def discover_assets(self):
        '''
        Returns *asset_info_list* with all the assets loaded in the current
        scene that has an ftrackAssetNode connected
        '''
        ftrack_asset_nodes = nuke_utils.get_nodes_with_ftrack_tab()
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
        self.logger.info("yep")
        self.logger.info("removing: --> {}".format(self.ftrack_object))
        if not self.ftrack_object:
            self.logger.info("There is no ftrack object")
            return

        self.logger.debug("Remove assetLink: {}".format(
            self.ftrack_object.knob(asset_const.ASSET_LINK).value()
        ))

        if self.ftrack_object.Class() == 'BackdropNode':
            nodes_to_delete_str = self.ftrack_object.knob(
                asset_const.ASSET_LINK
            ).value()
            nodes_to_delete = nodes_to_delete_str.split(";")
            for node_s in nodes_to_delete:
                node = nuke.toNode(node_s)
                self.logger.info("removing : {}".format(node.Class()))
                nuke.delete(node)

        ftrack_object = self.ftrack_object
        nuke.delete(ftrack_object)
        self.logger.info("Remove done")

    def _remove_asset(self, event):
        '''
        Override function from the main class, remove the current assets of the
        scene.
        '''
        super(FtrackAssetTab, self)._remove_asset(event)

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
        super(FtrackAssetTab, self)._select_asset(event)
        asset_item = event['data']

        self.ftrack_object['selected'].setValue(True)

        return asset_item

    def _clear_selection(self, event):
        '''
        Override function from the main class, select the current assets of the
        scene.
        '''
        super(FtrackAssetTab, self)._clear_selection(event)
        asset_item = event['data']

        nuke_utils.cleanSelection()

        return asset_item