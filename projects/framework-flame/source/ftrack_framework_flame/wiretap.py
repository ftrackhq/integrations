# coding: utf-8
# customised from # https://github.com/predat/wiretap/blob/master/src/wiretap/wiretap.py#L275

import logging
import pwd
import grp
import os

import sys
import platform
import pprint
import xml.dom.minidom as minidom

import flame

from adsk.libwiretapPythonClientAPI import (
    WireTapClientInit,
    WireTapClientUninit,
    WireTapNodeHandle,
    WireTapServerHandle,
    WireTapInt,
    WireTapStr,
)

logger = logging.getLogger(__name__)


class WiretapException(Exception):
    """Manage WireTap exceptions"""
    pass


class WiretapNodeType:
    Node = 'NODE'
    Project = 'PROJECT'
    User = 'USER'
    Workspace = 'WORKSPACE'
    Desktop = 'DESKTOP'
    Volume = 'VOLUME'
    Folder = 'FOLDER'
    Library = 'LIBRARY'
    LibraryList = 'LIBRARY_LIST'


class WiretapApi(object):

    def __init__(self, hostname='localhost'):
        super(WiretapApi, self).__init__()
        self.hostname = hostname

        # Initialize wiretap connection
        if not WireTapClientInit():
            msg = "Unable to initialize WireTap client API"
            logger.critical(msg)
            raise WiretapException(msg)

        self._server = WireTapServerHandle(f"{self.hostname}:IFFFS")

    def __del__(self):
        self._server = None
        WireTapClientUninit()

    @property
    def flame_version(self):
        return flame.get_version()

    def create_project(self, project_name, workspace_name='ftrack'):

        xml_settings = self._xml_settings(project_name=project_name)

        if not self._child_node_exists("/projects", project_name, WiretapNodeType.Project):
            logger.info(
                f"Project '{project_name}' does not exists. Create it with settings: \n{pprint.pformat(xml_settings)}"
            )

            volumes = self.get_volumes()
            logger.debug(f"Framestore found: {volumes}")

            if len(volumes) == 0:
                raise Exception("Cannot create project! There is no volumes defined for this flame.")

            # use the first volume available
            volume_node = self._get_node_from_path(f"/volumes/{volumes[0]}")

            if not volume_node:
                raise WiretapException("Unable to retrieve a volume.")
            else:
                self._create_node(volume_node, WiretapNodeType.Node, project_name)

                project_node = WireTapNodeHandle(self._server, f"/projects/{project_name}")
                if not project_node.setMetaData("XML", xml_settings):
                    raise WiretapException(f"Error setting metadata for {project_name}: {project_node.lastError()}")

                workspace_node = self._create_node(project_node, WiretapNodeType.Workspace, workspace_name)
                self._create_node(workspace_node, WiretapNodeType.Desktop)

                return project_node

    def create_user(self, user_name):
        users = WireTapNodeHandle(self._server, "/users")
        user_node = self._create_node(users, WiretapNodeType.User, user_name)

        user_nodes = [
            '2dtransform', '3dblur', 'CreatedBy', 'action', 'audio', 'automatte',
            'autostabilize', 'average', 'batch', 'batchclip', 'blur', 'bumpDisplace',
            'burnin', 'burnmetadata', 'channelEditor', 'check', 'clamp', 'colourframe',
            'colourpicker', 'colourwarper', 'combine', 'comp', 'composite', 'compound',
            'correct', 'damage', 'deal', 'deform', 'degrain', 'deinterlace',
            'deliverables', 'denoise', 'depthOfField', 'desktop', 'difference',
            'dissolve', 'distort', 'dve', 'edgeDetect', 'editdesk', 'exposure',
            'fieldmerge', 'filter', 'flip', 'gatewayImport', 'glow', 'gradient',
            'guides', 'hotkey', 'interlace', 'keyerChannel', 'keyerHLS', 'keyerRGB',
            'keyerRGBCMYL', 'keyerYUV', 'letterbox', 'logicop', 'logo', 'look',
            'lut', 'mapConvert', 'mask', 'matchbox', 'mediaImport', 'modularKeyer',
            'mono', 'morf', 'motif', 'motionAnalyse', 'motionBlur', 'paint',
            'pixelspread', 'play', 'posterize', 'pulldown', 'pybox', 'recursiveOps',
            'regrain', 'resize', 'separate', 'stabilizer', 'status', 'stereo',
            'stereoAnaglyph', 'stereoInterlace', 'stereoToolbox', 'stylize',
            'substance', 'tangentPanel', 'text', 'timewarp', 'tmp', 'vectorViewer', 'viewing'
        ]

        for node in user_nodes:
            self._create_node(parent=user_node, node_type=WiretapNodeType.Node, node_name=node)

        return user_node

    def get_projects(self):
        projects_node = self._get_node_from_path('/projects')
        children = self._get_children(projects_node)
        return list(children.keys())

    def get_project(self, project_name):
        return self._get_node_from_path(f"/projects/{project_name}")

    def get_users(self):
        users_node = self._get_node_from_path('/users')
        children = self._get_children(users_node)
        return list(children.keys())

    def get_user(self, user_name):
        return self._get_node_from_path(f"/users/{user_name}")

    def delete_user(self, user_name):
        user_node = self.get_user(user_name)
        if not user_node.destroyNode():
            raise WiretapException(f"Unable to delete user {user_name}: {user_node.lastError()}")

    def get_volumes(self):
        volumes_node = self._get_node_from_path('/volumes')
        children = self._get_children(volumes_node)
        return list(children.keys())

    def _create_node(self, parent, node_type, node_name=None):
        node_name = node_type.title() if not node_name else node_name
        node = WireTapNodeHandle()
        if not parent.createNode(node_name, node_type, node):
            raise WiretapException(f"Unable to create node: {parent.lastError()}")

        return node

    def _create_project_libraries(self, parent, library_name, libraries_dict):
        library_node = self._get_node(parent, library_name, WiretapNodeType.LibraryList)
        for lib in libraries_dict.keys():
            lib_node = self._create_node(library_node, WiretapNodeType.Library, lib)

            if libraries_dict[lib]:
                for folder in libraries_dict[lib]:
                    self._create_node(lib_node, WiretapNodeType.Folder, folder)

    def _get_project_metadata(self, project_node):
        if project_node is not None:
            xml = WireTapStr()
            project_node.getMetaData("XML", "", 1, xml)

            pretty_xml = minidom.parseString(xml.c_str()).toprettyxml()
            return pretty_xml

    def _get_node_from_path(self, path):
        node = WireTapNodeHandle(self._server, path)

        node_name = WireTapStr()
        if node.getDisplayName(node_name):
            return node
        else:
            return None

    def _get_children(self, parent):
        children = dict()
        num_children = WireTapInt(0)
        if not parent.getNumChildren(num_children):
            raise WiretapException(f"Unable to obtain number of volumes: {parent.lastError()}")

        child_obj = WireTapNodeHandle()
        for child_idx in range(num_children):
            if not parent.getChild(child_idx, child_obj):
                raise WiretapException(f"Unable to get child: {parent.lastError()}")

            node_name = WireTapStr()
            if not child_obj.getDisplayName(node_name):
                raise WiretapException(f"Unable to get child name: {child_obj.lastError()}")

            children[str(node_name)] = child_obj
        return children

    def _get_node(self, parent_node, node_name, node_type):
        parent_node_name = WireTapStr()

        if not parent_node.getDisplayName(parent_node_name):
            raise WiretapException(f"Couldn't get node name:{ parent_node.lastError()}")
        logger.debug("parent node name: %s" % parent_node_name)

        num_children = WireTapInt(0)
        if not parent_node.getNumChildren(num_children):
            raise WiretapException(
                f"Couldn't get children number for the node {parent_node_name.c_str()}: {parent_node.lastError()}"
            )
        logger.debug("parent num children: %s" % int(num_children))

        result_node = None
        child_node = WireTapNodeHandle()
        child_node_type = WireTapStr()
        child_node_name = WireTapStr()

        # iterate over children
        for child_idx in range(num_children):
            # get child node
            if not parent_node.getChild(child_idx, child_node):
                raise WiretapException(f"Unable to get child: {parent_node.lastError()}")
            logger.debug("child: %s" % child_node)

            # get child node name
            if not child_node.getDisplayName(child_node_name):
                raise WiretapException(f"Couldn't get node name: {child_node.lastError()}")
            logger.debug("child node name: %s" % child_node_name.c_str())

            # get child node type
            if not child_node.getNodeTypeStr(child_node_type):
                raise WiretapException(f"Couldn't get node type: {child_node.lastError()}")
            logger.debug("child node type: %s" % child_node_type.c_str())

            # check if child match criteria
            if child_node_name.c_str() == node_name and child_node_type.c_str() == node_type:
                result_node = child_node
                logger.debug("node found !")
                break

            result_node = self._get_node(child_node, node_name, node_type)
            if result_node:
                logger.debug("node found !")
                return result_node

        return result_node

    def _child_node_exists(self, parent_path, child_name, child_type):
        # get the parent
        parent = WireTapNodeHandle(self._server, parent_path)

        # get number of children
        num_children = WireTapInt(0)
        if not parent.getNumChildren(num_children):
            raise WiretapException(
                "Wiretap error: Unable to obtain number of "
                "children for node %s> Please check that your "
                "wiretap service is running. "
                f"Error reported: {parent_path, parent.lastError()}"
            )

        # iterate over children, look for the given node
        child_obj = WireTapNodeHandle()
        for child_idx in range(num_children):
            # get the child
            if not parent.getChild(child_idx, child_obj):
                raise WiretapException(f"Unable to get child: {parent.lastError()}")

            node_name = WireTapStr()
            node_type = WireTapStr()

            if not child_obj.getDisplayName(node_name):
                raise WiretapException(f"Unable to get child: {child_obj.lastError()}")

            if not child_obj.getNodeTypeStr(node_type):
                raise WiretapException(f"Unable to obtain child type: {child_obj.lastError()}")

            if node_name.c_str() == child_name and node_type.c_str() == child_type:
                return True

        return False

    def _xml_settings(self, project_name, volume, fps=25, width=1920, height=1080,depth='10-bit'):
        # https://help.autodesk.com/view/FLAME/2024/ENU/?guid=Flame_API_Wiretap_SDK_Media_and_Metadata_Formats_Project_Node_Metadata_XML_html

        ratio = str(float(width)/float(height))
        project_xml_data = f"""
        <Project>
        <Name>{project_name}</Name>
        <Description>"Created with ftrack integration for flame: "</Description>
        <Partition>{volume}</Partition>
        <Version>{self.flame_version}</Version>
        <FrameWidth>{width}<FrameWidth>
        <FrameHeight>{height}<FrameHeight>
        <FrameDepth>{depth}</FrameDepth>
        <AspectRatio>{ratio:.5f}</AspectRatio>
        <FieldDominance>PROGRESSIVE</FieldDominance>
        <FrameRate>{fps} fps</FrameRate>
        <DefaultStartFrame>1001</DefaultStartFrame>
        <VisualDepth>unknown</VisualDepth>
        </Project>
        """
        return project_xml_data
