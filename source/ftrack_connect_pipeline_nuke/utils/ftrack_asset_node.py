from ftrack_connect_pipeline.asset import FtrackAssetInfo, FtrackAssetBase
from ftrack_connect_pipeline_nuke.constants import asset as asset_const

import nuke

class FtrackAssetTab(FtrackAssetBase):
    '''
    Base FtrackAssetNode class.
    '''

    @property
    def tabs(self):
        return self._tabs[:]

    @property
    def tab(self):
        return self._tab

    def is_sync(self):
        return self._check_tab_sync()

    def __init__(self, ftrack_asset_info, session):
        '''
        Initialize FtrackAssetTab with *ftrack_asset_info*, and *session*.

        *ftrack_asset_info* should be the
        :class:`ftrack_connect_pipeline.asset.asset_info.FtrackAssetInfo`
        instance.
        *session* should be the :class:`ftrack_api.session.Session` instance
        to use for communication with the server.
        '''
        super(FtrackAssetTab, self).__init__(ftrack_asset_info, session)

        self.scene_node = None

        self._tab = None
        self._tabs = []

    def _set_tab(self, ftrack_tab):
        '''
        Sets the given *ftrack_tab* as the current self._tab of the class
        '''
        self._tab = ftrack_tab

    def init_tab(self, scene_node):
        '''
        Return the scene node for this class. It checks if there is already a
        matching ftrack tab in the scene, and the tab if needed. In case there
        is no ftrack tab in the scene this function creates a new one on the
        given *scene_node*.

        *scene_node*: Should be the string name of the scene node where you want
        to add the ftrack tab
        '''

        self.scene_node = nuke.toNode(scene_node)

        ftrack_tab = self.get_ftrack_tab_from_nuke_obj()
        if ftrack_tab:
            self._set_tab(ftrack_tab)
            if not self.is_sync():
                self._update_tab()
        else:
            self.create_new_tab()

        return self.scene_node

    def _get_parameters_dictionary(self):
        '''
        Returns a dicctionary with the matching keys and values of the asset info
        if the current scene_node have the ftrack tab.
        '''
        param_dict = {}
        for knob in self.scene_node.allKnobs():
            if knob.name() in asset_const.KEYS:
                param_dict[knob.name()] = knob.getValue()
        return param_dict

    def get_ftrack_tab_from_nuke_obj(self):
        '''
        Return the ftrack tab knob of the current scene node in case the tab
        exists and the values match the asset info values.
        '''
        for knob in self.scene_node.allKnobs():
            if asset_const.FTRACK_PLUGIN_TYPE in knob.name():
                param_dict = self._get_parameters_dictionary()
                node_asset_info = FtrackAssetInfo(param_dict)
                if node_asset_info.is_deprecated:
                    raise DeprecationWarning(
                        "Can not read v1 ftrack asset plugin")
                if (
                        node_asset_info[asset_const.COMPONENT_ID] ==
                        self.asset_info[asset_const.COMPONENT_ID]
                ):
                    return knob

    def _check_tab_sync(self):
        '''
        Check if the current parameters of the ftrack tab match the values
        of the asset_info.
        '''
        if not self._tab or not self.scene_node:
            self.logger.warning("Ftrack tab doesn't exists")
            return False

        synced = False

        param_dict = self._get_parameters_dictionary()
        node_asset_info = FtrackAssetInfo(param_dict)

        if node_asset_info == self.asset_info:
            self.logger.debug("{} is synced".format(self.scene_node))
            synced = True

        return synced

    def create_new_tab(self):
        '''
        Creates an ftrack tab to the current scene_node.
        '''
        self._tab = nuke.Tab_Knob(asset_const.FTRACK_PLUGIN_TYPE, 'ftrack')
        self.scene_node.addKnob(self.tab)

        for k in self.asset_info.keys():
            knob = nuke.String_Knob(k)
            self.scene_node.addKnob(knob)

        self._set_node_color(self.scene_node)

        self._tabs.append(self.tab)

        return self._update_tab()

    def _update_tab(self):
        '''
        Update the parameters of the ftrack tab. And Return the scene node
        updated
        '''

        for k, v in self.asset_info.items():
            self.scene_node.knob(k).setValue(str(v))

        return self.scene_node

    def _set_node_color(self, scene_node, latest=True):
        # Green RGB 20, 161, 74
        # Orange RGB 227, 99, 22
        latest_color = int('%02x%02x%02x%02x' % (20, 161, 74, 255), 16)
        old_color = int('%02x%02x%02x%02x' % (227, 99, 22, 255), 16)
        if latest:
            scene_node.knob("note_font_color").setValue(latest_color)
        else:
            scene_node.knob("note_font_color").setValue(old_color)
