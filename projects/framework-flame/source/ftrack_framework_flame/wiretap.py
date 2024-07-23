import logging
import subprocess
import platform
import flame

from adsk.libwiretapPythonClientAPI import (
    WireTapClientInit,
    WireTapClientUninit,
    WireTapNodeHandle,
    WireTapServerHandle,
    WireTapInt,
    WireTapStr,
)

class WiretapApiError(Exception):
    pass



class WiretapApi(object):
    install_root = "/opt/Autodesk

    @property
    def flame_version(self):
        return flame.get_version(),

    @property
    def wiretap_tools(self):
        return f'{self.install_root}/wiretap/tools/{self.flame_version}/'

    @property
    def server(self):
        return self._server

    def __init__(self):
        WireTapClientInit()

        super(WiretapApi, self).__init__()
        self._server_id = "localhost:IFFFS"
        self._server = WireTapServerHandle(self._server_id)

    def close(self):
        self._server = None
        self._server_id = None
        WireTapClientUninit()

    @property
    def volumes(self):
        available_volumes = []

        volume_node = WireTapNodeHandle(self.server, "/volumes")
        children = WireTapInt(0)
        if not volume_node.getNumChildren(children):
            raise WiretapApiError(
                f"No child volume found {volume_node.lastError()}"
            )

        child_node = WireTapNodeHandle()
        for c_idx in range(children):

            # get the child
            if not volume_node.getChild(c_idx, child_node):
                raise WiretapApiError(f"Cannot find child: {volume_node.lastError()}")

            node_name = WireTapStr()

            if not child_node.getDisplayName(node_name):
                raise WiretapApiError(
                    f"Cannot find child name: {node_name.lastError()}"
                )

            available_volumes.append(node_name.c_str())

        return available_volumes

    def ensure_project(self, project, user, workspace):
        project_exists = self.__check_child_node("/projects", project, "PROJECT")
        if not project_exists:


    def ensure_workspace(self, project, workspace):
        workspace_exists = self.__check_child_node(f"/projects/{project}", workspace, "WORKSPACE")
        if not workspace_exists:
            project_node = WireTapNodeHandle(self.server, f"/projects/{project}")

            node = WireTapNodeHandle()
            if not project_node.createNode(workspace, "WORKSPACE", node):
                raise WiretapApiError(f'Cannot create workspace {workspace} for project {project}. Error {project.lastError()}')

        return True

    def ensure_user(self, user):
        if not self.__check_child_node("/", "users", "USERS"):
            return False

        if not self.__check_child_node("/users", user, "USER"):
            users_node = WireTapNodeHandle(self.server, "/users")
            node = WireTapNodeHandle()

            if not users_node.createNode(user, "USER", node):
                raise WiretapApiError(f'Cannot create user {user} . Error {users_node.lastError()}')

        return True

    def __check_child_node(self, parent, child, type):
        parent_node = WireTapNodeHandle(self._server, parent)
        children = WireTapInt(0)
        if not parent_node.getNumChildren(children):
            raise WiretapApiError(f'Node {parent}, has no child. Error {parent.lastError()}')

        child_node = WireTapNodeHandle()
        for c_idx in range(children):
            if not parent.getChild(c_idx, child_node):
                raise WiretapApiError(f'Node {parent}, has no child. Error {parent.lastError()}')

            node_name = WireTapStr()
            node_type = WireTapStr()

            if not child_node.getDisplayName(node_name):
                raise WiretapApiError(f'Cannot get child name. Error {child_node.lastError()}')

            if not child_node.getNodeTypeStr(node_type):
                raise WiretapApiError(f'Cannot get child type. Error {child_node.lastError()}')

            if node_name.c_str() == child and node_type.c_str() == type:
                return True

        return False
