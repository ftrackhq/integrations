# :coding: utf-8
# :copyright: Copyright (c) 2025 ftrack

import sys
import json
import tempfile
import base64
import traceback
import os
from uuid import uuid1 as uuid


import logging


from rv import commands as rvc
from rv import extra_commands as rve
from rv import runtime as rvr


ftrack_rv_logger_name = "ftrack_rv"


try:
    import ftrack_logging

    ftrack_logging.configure_logging(ftrack_rv_logger_name)
    # Setup logging.
except Exception as error:
    logging.warning("Failed to Initialize logging.", error)

logger = logging.getLogger(ftrack_rv_logger_name)
logger.debug(f'PY3 Enabled: {os.environ.get("RV_PYTHON3", "NOT SET")}')
logger.debug(f"Interpreter {sys.executable}")
logger.debug(f"version {sys.version_info}")


# Check for base environment presence.
required_envs = ["FTRACK_SERVER", "FTRACK_API_KEY"]
for env in required_envs:
    if env not in os.environ:
        logger.error(f"{env} environment not found!")


# Setup ssl certificate path.
cacert_path = os.path.join(os.path.dirname(__file__), "cacert.pem")
os.environ["REQUESTS_CA_BUNDLE"] = cacert_path

# Setup dependencies path.
dependencies_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "dependencies.zip")
)

logger.debug(f"Adding {dependencies_path} to PATH")
sys.path.insert(0, dependencies_path)


# Try import ftrack's new API.
try:
    import ftrack_api
    from ftrack_api.symbol import ORIGIN_LOCATION_ID, SERVER_LOCATION_ID

except ImportError:
    logger.error(f"No Ftrack API module found in {dependencies_path}")
    raise


# Cache to keep track of filesystem path for components.
# This will cause the component to use the same filesystem path
# during the entire session.
componentFilesystemPaths = {}

sequenceSourceNode = None
stackSourceNode = None
layoutSourceNode = None

# Store references to annotation components being uploaded between methods.
annotation_components = {}


# Initialize New API. Failures are captured so the module still imports;
# callers (see ftrack.py) check ``session is None`` / ``session_init_error``
# and render an error panel instead of crashing the plugin.
session = None
origin_location = None
server_location = None
session_init_error = ""
session_init_reason = ""
try:
    session = ftrack_api.Session(auto_connect_event_hub=False)

    # Get some useful locations.
    origin_location = session.get("Location", ORIGIN_LOCATION_ID)
    server_location = session.get("Location", SERVER_LOCATION_ID)

except Exception as exception:
    logger.exception("Failed to initialize ftrack API session.")
    session = None
    origin_location = None
    server_location = None
    session_init_error = traceback.format_exc()
    session_init_reason = (
        "Could not connect to the ftrack server. Verify FTRACK_SERVER "
        "and FTRACK_API_KEY are set (or pass ftrackUrl=... via rvlink), "
        f"then restart RV. ({type(exception).__name__}: {exception})"
    )


def _getSourceNode(nodeType="sequence"):
    """
    Return the source node of the specified type (sequence, stack, or layout).

    This method creates a source node if it doesn't already exist, and returns a reference
    to it. The node is created with a specific type and given a UI name for display.

    Args:
        nodeType (str): Type of node to create. Options are 'sequence', 'stack', or 'layout'.
                        Defaults to 'sequence'.

    Returns:
        rv.commands.Node: The created source node or previously created instance.

    Raises:
        Exception: If there's an issue creating or accessing the node.
    """
    global sequenceSourceNode
    global stackSourceNode
    global layoutSourceNode

    if nodeType == "sequence":
        if sequenceSourceNode is None:
            sequenceSourceNode = rvc.newNode("RVSequenceGroup", "Sequence")

            rve.setUIName(sequenceSourceNode, "SequenceNode")

        return sequenceSourceNode

    elif nodeType == "stack":
        if stackSourceNode is None:
            stackSourceNode = rvc.newNode("RVStackGroup", "Stack")

            rve.setUIName(stackSourceNode, "StackNode")

        return stackSourceNode

    elif nodeType == "layout":
        if layoutSourceNode is None:
            layoutSourceNode = rvc.newNode("RVLayoutGroup", "Layout")

            rve.setUIName(layoutSourceNode, "LayoutNode")

        return layoutSourceNode


def _setWipeMode(state):
    """
    Set the wipe mode state in RV.

    This utility function toggles the wipe mode in RV based on the current state.
    It checks if wipes are currently shown and toggles accordingly.

    Args:
        state (bool): True to enable wipe mode, False to disable it.

    Returns:
        None
    """
    if rvr.eval("rvui.wipeShown()", ["rvui"]) != -1 and state is False:
        rvr.eval("rvui.toggleWipe()", ["rvui"])

    if rvr.eval("rvui.wipeShown()", ["rvui"]) == -1 and state is True:
        rvr.eval("rvui.toggleWipe()", ["rvui"])


def _getFilePath(componentId):
    """
    Return a filesystem path for a component based on its ID.

    This method retrieves the filesystem path for a component from the session.
    If the path isn't cached, it fetches it from the session and caches it for future use.

    Args:
        componentId (str): The ID of the component to get the path for.

    Returns:
        str: The filesystem path of the component.

    Raises:
        Exception: If the component cannot be found or accessed.
    """
    global componentFilesystemPaths
    path = componentFilesystemPaths.get(componentId, None)
    logger.debug(f"_getFilePath {componentId} :: {path}")

    if path is None:
        ftrack_component = session.get("Component", componentId)
        location = session.pick_location(component=ftrack_component)
        path = location.get_filesystem_path(ftrack_component)
        logger.debug(f"adding {componentId} to {componentFilesystemPaths}")
        componentFilesystemPaths[componentId] = path

    return path


def _ftrackAddVersion(track, layout):
    """
    Add a version of a track to a layout in RV.

    This method creates a new source node for a track and connects it to the specified layout.
    It also sets a UI name for the new source node.

    Args:
        track (str): The track to add as a version.
        layout (str): The layout to add the track to (e.g., 'defaultLayout').

    Returns:
        rv.commands.Node: The newly created source node.
    """
    stackInputs = rvc.nodeConnections(layout, False)[0]
    newSource = rvc.addSourceVerbose([track], None)
    rvc.setNodeInputs(layout, stackInputs)
    rve.setUIName(rvc.nodeGroup(newSource), track)

    return newSource


def _ftrackCreateGroup(tracks, sourceNode, layout):
    """
    Create a group of tracks in RV with a common source node.

    This method creates a group of source nodes for multiple tracks and connects them
    to a source node. Each track is processed individually and added to the group.

    Args:
        tracks (list): List of track IDs to create a group for.
        sourceNode (rv.commands.Node): The source node to connect the tracks to.
        layout (str): The layout to use for the group (e.g., 'defaultLayout').

    Returns:
        None
    """
    singleSources = []
    for track in tracks:
        try:
            singleSources.append(
                rvc.nodeGroup(_ftrackAddVersion(track, layout))
            )
        except Exception as error:
            logger.exception(error)

    rvc.setNodeInputs(sourceNode, singleSources)


def loadPlaylist(playlist, index=None, includeFrame=None):
    """
    Load a playlist of components into RV.

    This method loads a playlist of component paths into RV and optionally jumps to
    a specific index or frame. It creates source nodes for each component and sets
    up the appropriate layout.

    Args:
        playlist (list): List of component dictionaries containing 'componentId'.
        index (int, optional): Index in the playlist to jump to after loading. Defaults to None.
        includeFrame (str, optional): Frame reference to include when loading. Defaults to None.

    Returns:
        None
    """
    _setWipeMode(False)
    startFrame = 1

    if not includeFrame == "false":
        startFrame = rve.sourceFrame(rvc.frame(), None)

    for oldSource in rvc.nodesOfType("RVSourceGroup"):
        rvc.deleteNode(oldSource)

    sources = []
    for item in playlist:
        sources.append(_getFilePath(item.get("componentId")))

    sequenceSourceNode = _getSourceNode("sequence")

    _ftrackCreateGroup(sources, sequenceSourceNode, "defaultLayout")
    rvc.setViewNode(sequenceSourceNode)

    if index:
        ftrackJumpTo(index, startFrame)


def validateComponentLocation(componentId, versionId):
    """
    Validate if a component is accessible in a local location.

    This method checks if a component can be accessed in a local location. If not,
    it sends an internal event to ftrack to break the item.

    Args:
        componentId (str): The ID of the component to validate.
        versionId (str): The version ID of the component.

    Returns:
        None
    """

    try:
        _getFilePath(componentId)
    except Exception:
        logger.warning(
            f'Component with Id "{componentId}" is not available in any location.'
        )
        try:
            rvc.sendInternalEvent(
                "ftrack-event",
                base64.b64encode(
                    json.dumps(
                        {"type": "breakItem", "versionId": versionId}
                    ).encode("utf-8")
                ).decode("ascii"),
                None,
            )
        except Exception:
            logger.error("Could not send internal event to ftrack.")


def ftrackCompare(data):
    """
    Activate compare mode in RV between two components.

    This method activates compare mode in RV between two components (A and B) with
    different modes (wipe, load, etc.). It creates source nodes for the components
    and sets up the appropriate layout.

    Args:
        data (dict): Dictionary containing componentIdA, componentIdB, and mode.
                     mode can be 'wipe', 'load', or other values.

    Returns:
        None
    """
    _setWipeMode(False)
    startFrame = 1
    try:
        startFrame = rve.sourceFrame(rvc.frame(), None)
    except Exception:
        pass

    componentIdA = data.get("componentIdA")
    componentIdB = data.get("componentIdB")
    mode = data.get("mode")

    trackA = _getFilePath(componentIdA)

    layout = "defaultStack" if mode == "wipe" else "defaultLayout"

    if not mode == "load":
        trackB = _getFilePath(componentIdB)

        try:
            if mode == "wipe":
                sourceNode = _getSourceNode("stack")
                _ftrackCreateGroup([trackA, trackB], sourceNode, layout)
                rvc.setViewNode(sourceNode)
                rvr.eval("rvui.toggleWipe()", ["rvui"])
            else:
                sourceNode = _getSourceNode("layout")
                _ftrackCreateGroup([trackA, trackB], sourceNode, layout)
                rvc.setViewNode(sourceNode)
        except Exception:
            print(traceback.format_exc())
    else:
        sourceNode = _getSourceNode("layout")
        _ftrackCreateGroup([trackA], sourceNode, layout)
        rvc.setViewNode(sourceNode)

    if startFrame > 1:
        rvc.setFrame(startFrame)


def _getEntityFromEnvironment():
    """
    Extract entity information from environment variables.

    This method checks for an environment variable containing event data and
    extracts selection information (entityId and entityType) from it.

    Returns:
        tuple: (entityId, entityType) if found, otherwise (None, None).
    """
    # Check for environment variable specifying additional information to
    # use when loading.
    eventEnvironmentVariable = "FTRACK_CONNECT_EVENT"

    eventData = os.environ.get(eventEnvironmentVariable)

    if eventData is not None:
        try:
            decodedEventData = json.loads(base64.b64decode(eventData))
        except (TypeError, ValueError):
            logger.error(
                f"Failed to decode {eventEnvironmentVariable}: {eventData}"
            )
        else:
            selection = decodedEventData.get("selection", [])
            logger.info(f"selection {selection}")
            # At present only a single entity which should represent an
            # ftrack List is supported.
            if selection:
                try:
                    entity = selection[0]
                    entityId = entity.get("entityId")
                    entityType = entity.get("entityType")
                    return entityId, entityType
                except (IndexError, AttributeError, KeyError):
                    logger.error(
                        f"Failed to extract selection information from: {selection}"
                    )
    else:
        logger.debug(
            f"No event data retrieved. {eventEnvironmentVariable} not set."
        )

    return None, None


def getNavigationURL(params=None):
    """
    Return URL to navigation panel in ftrack.

    Returns an empty string when no URL can be generated. Use
    :func:`_generateURL` directly when you also need the failure reason.
    """
    url, _reason = _generateURL(params, "review_navigation")
    return url


def getActionURL(params=None):
    """
    Return URL to action panel in ftrack.

    Returns an empty string when no URL can be generated. Use
    :func:`_generateURL` directly when you also need the failure reason.
    """
    url, _reason = _generateURL(params, "review_action")
    return url


def _translateEntityType(entityType):
    """
    Translate an entity type to a format usable with the ftrack API.

    This method converts an entity type (with underscores) to a lower-case format
    that can be used with the ftrack API. It checks schemas to find the appropriate
    ID for the entity type.

    Args:
        entityType (str): The entity type to translate (e.g., "project", "asset").

    Returns:
        str: The translated entity type ID.

    Raises:
        ValueError: If the entity type cannot be translated.
    """
    # Get entity type and make sure it is lower cased. Most places except
    # the component tab in the Sidebar will use lower case notation.
    entity_type = entityType.replace("_", "").lower()

    for schema in session.schemas:
        alias_for = schema.get("alias_for")

        if (
            alias_for
            and isinstance(alias_for, str)
            and alias_for.lower() == entity_type
        ):
            return schema["id"]

    for schema in session.schemas:
        if schema["id"].lower() == entity_type:
            return schema["id"]

    raise ValueError(f"Unable to translate entity type: {entity_type}.")


def _get_temp_data_url(name, temp_data_id):
    """
    Generate a URL for temporary data in ftrack.

    This method creates a URL for temporary data with the specified name and ID.

    Args:
        name (str): The name of the widget.
        temp_data_id (str): The ID of the temporary data.

    Returns:
        str: Full URL with entityType and entityId parameters.
    """
    operation = {
        "action": "get_widget_url",
        "name": name,
        "theme": None,
    }

    result = session.call([operation])
    url = result[0]["widget_url"]
    full_url = f"{url}&entityType=tempdata&entityId={temp_data_id}"
    return full_url


def _generateURL(params=None, panelName=None):
    """
    Generate a URL to a ftrack panel based on parameters.

    Args:
        params: Parameters string (JSON) to use for generating the URL.
        panelName: Name of the panel to generate URL for.

    Returns:
        tuple[str, str]: ``(url, reason)``. ``url`` is the resolved panel URL,
        or an empty string when no URL could be generated. When ``url`` is
        empty, ``reason`` is a human-readable explanation that callers can
        surface in the UI; otherwise ``reason`` is empty.
    """
    logger.info(f"_generateURL with params: {params}")
    if session is None:
        return "", session_init_reason
    url = ""
    reason = ""
    try:
        entityId = None
        entityType = None
        context_provided = bool(params) or bool(
            os.environ.get("FTRACK_CONNECT_EVENT")
        )

        if params:
            panelName = panelName or params
            try:
                params = json.loads(params)
                entityId = params["entityId"][0]
                entityType = params["entityType"][0]
            except Exception:
                entityId, entityType = _getEntityFromEnvironment()
        else:
            entityId, entityType = _getEntityFromEnvironment()

        if not (entityId and entityType):
            if context_provided:
                reason = (
                    "A launch context was provided but did not contain a "
                    "valid entity selection. See the ftrack-rv log for "
                    "details."
                )
            else:
                reason = (
                    "No entity selection was provided. Launch RV from "
                    "ftrack Connect with a Task, AssetVersion, or List "
                    "selected, or open a review link from the ftrack web "
                    "UI via the rvlink:// protocol handler."
                )
        elif entityType != "tempdata":
            new_entity = None
            try:
                new_entity_type = _translateEntityType(entityType)
                new_entity = session.get(new_entity_type, entityId)
            except Exception as exception:
                logger.error(str(exception))
                reason = (
                    f'Failed to look up {entityType} {entityId} on '
                    f'{os.environ.get("FTRACK_SERVER", "the ftrack server")}: '
                    f'{exception}'
                )

            if new_entity is None and not reason:
                reason = (
                    f'Could not find {entityType} with id {entityId} on '
                    f'{os.environ.get("FTRACK_SERVER", "the ftrack server")}.'
                )
            elif new_entity is not None:
                try:
                    url = session.get_widget_url(panelName, entity=new_entity)
                except Exception as exception:
                    logger.error(str(exception))
                    reason = (
                        f"ftrack returned an error while fetching the "
                        f"{panelName} panel URL: {exception}"
                    )
        else:
            try:
                url = _get_temp_data_url(panelName, entityId)
            except Exception as exception:
                logger.error(str(exception))
                reason = f"Failed to load temporary data panel: {exception}"

        logger.info(f'Returning url "{url}" reason "{reason}"')
    except Exception as error:
        logger.exception(f"Failed to generate URL. {error}")
        reason = f"Unexpected error generating URL: {error}"
    return url, reason


def ftrackFilePath(id):
    """
    Generate a temporary file path for a component.

    This method creates a temporary file path based on the provided ID.

    Args:
        id (str): The ID to use for the filename.

    Returns:
        str: The temporary file path.
    """
    try:
        if id != "":
            filename = "%s.jpg" % id
            filepath = os.path.join(tempfile.gettempdir(), filename)
        else:
            filepath = tempfile.gettempdir()
        return filepath
    except Exception:
        logger.exception("Failed to get file path.")
        return ""


def ftrackUUID():
    """
    Generate a UUID based on uuid1.

    This method returns a string representation of a UUID.

    Returns:
        str: UUID string.
    """
    return str(uuid())


def ftrackJumpTo(index=0, startFrame=1):
    """
    Move the RV playhead to a specific index and frame.

    This method calculates the frame number based on the index and moves the playhead
    to that position.

    Args:
        index (int): The index in the playlist to jump to.
        startFrame (int): The starting frame to use when jumping.

    Returns:
        None
    """
    try:
        index = int(index)
        frameNumber = 0

        for idx, source in enumerate(rvc.nodesOfType("RVFileSource")):
            if not idx >= index:
                data = rvc.sourceMediaInfoList(source)[0]
                add = (data.get("endFrame", 0) - data.get("startFrame", 0)) + 1
                add = 1 if add == 0 else add
                frameNumber += add

        rvc.setFrame(frameNumber + startFrame)
    except Exception:
        logger.exception("Failed to jump to index.")


def create_component(encoded_args):
    """Create a component without adding it to a location.

    This function creates a component from the provided encoded arguments and stores
    a reference to it in the annotation_components dictionary. The component is not
    associated with any specific location.

    Args:
        encoded_args (str): A JSON-encoded dictionary containing the following keys:
            - file_name (str): The name of the file associated with the component.
            - frame (int): The frame number associated with the component.

    Returns:
        None: The function stores the component reference in annotation_components
              but does not return a value.

    Note:
        This function is used to create components for later use in annotations
        without immediately associating them with a specific location. The component
        reference is stored in the annotation_components dictionary for future reference.
    """
    component_id = None
    try:
        args = json.loads(encoded_args)
        file_name = args["file_name"]
        frame = args["frame"]

        component_name = f"Frame_{frame}"
        file_path = os.path.join(ftrackFilePath(""), file_name)
        logger.info(rf"Creating component: {file_path}")
        component = session.create_component(
            path=file_path, data=dict(name=component_name), location=None
        )
        component_id = component["id"]
        annotation_components[component_id] = component
    except Exception:
        logger.exception("Failed to create component.")

    return component_id


def upload_component(component_id):
    """
    Add a component with the given component_id to the ftrack server location.

    This function retrieves the component from the annotation_components dictionary
    and adds it to the specified server location. After successful addition,
    the component is removed from the annotation_components dictionary to prevent
    duplicate processing.

    Args:
        component_id (str): The unique identifier of the component to upload.

    Returns:
        str: The component_id if successful, None if an error occurs.

    Raises:
        Exception: If there's an issue adding the component to the server location.

    """
    try:
        logger.info(
            f"Adding component {component_id} to ftrack server location."
        )
        component = annotation_components[component_id]
        server_location.add_component(component, origin_location)
        del annotation_components[component_id]
    except Exception:
        logger.exception("Failed to upload component")
    else:
        return component_id
