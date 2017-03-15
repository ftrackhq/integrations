# :coding: utf-8
# :copyright: Copyright (c) 2014 ftrack

import json
import tempfile
import base64
import traceback
import os
from uuid import uuid1 as uuid
import logging

import rv.commands
import rv.rvtypes
import rv.extra_commands
import rv.rvui
import rv.runtime
import rv as rv

import ftrack
from ftrack_api import Session

import ftrack_logging

ftrack_logging.setup()
logger = logging.getLogger('ftrack_connect_rv')

# Cache to keep track of filesystem path for components.
# This will cause the component to use the same filesystem path
# during the entire session.
componentFilesystemPaths = {}

sequenceSourceNode = None
stackSourceNode = None
layoutSourceNode = None

# Store references to annotation components being uploaded between methods.
annotation_components = {}


try:
    ftrack.setup(actions=False)
except:
    pass


session = Session(
    server_url=os.getenv("FTRACK_SERVER"),
    api_user=os.getenv("FTRACK_API_USER"),
    api_key=os.getenv("FTRACK_API_KEY", os.getenv('FTRACK_APIKEY')),
    auto_connect_event_hub=False
)


def _getSourceNode(nodeType='sequence'):
    '''Return source node of *nodeType*.'''
    global sequenceSourceNode
    global stackSourceNode
    global layoutSourceNode

    if nodeType == 'sequence':
        if sequenceSourceNode is None:
            sequenceSourceNode = rv.commands.newNode(
                'RVSequenceGroup', 'Sequence'
            )

            rv.extra_commands.setUIName(
                sequenceSourceNode, 'SequenceNode'
            )

        return sequenceSourceNode

    elif nodeType == 'stack':
        if stackSourceNode is None:
            stackSourceNode = rv.commands.newNode(
                'RVStackGroup', 'Stack'
            )

            rv.extra_commands.setUIName(
                stackSourceNode, 'StackNode'
            )

        return stackSourceNode

    elif nodeType == 'layout':
        if layoutSourceNode is None:
            layoutSourceNode = rv.commands.newNode(
                'RVLayoutGroup', 'Layout'
            )

            rv.extra_commands.setUIName(
                layoutSourceNode, 'LayoutNode'
            )

        return layoutSourceNode


def _setWipeMode(state):
    '''Util to set the state of wipes instead of toggle.'''
    if rv.runtime.eval('rvui.wipeShown()', ['rvui']) != -1 and state is False:
        rv.runtime.eval('rvui.toggleWipe()', ['rvui'])

    if rv.runtime.eval('rvui.wipeShown()', ['rvui']) == -1 and state is True:
        rv.runtime.eval('rvui.toggleWipe()', ['rvui'])


def _getFilePath(componentId):
    '''Return a single access path based on *source* and *location*'''
    global componentFilesystemPaths

    path = componentFilesystemPaths.get(componentId, None)

    if path is None:
        location = session.pick_location()
        ftrack_component = session.get('FileComponent', componentId)

        component_availability = ftrack_component.get_availability(
            [location]
        )

        availability = component_availability.values()[0]

        if availability != 100.0:
            raise IOError(
                'Could not retrieve file path for component {0} as no '
                'location for component accessible.'.format(
                    ftrack_component['name']
                )
            )

        path = location.get_filesystem_path(ftrack_component)
        componentFilesystemPaths[componentId] = path

        return path


def _ftrackAddVersion(track, layout):
    stackInputs = rv.commands.nodeConnections(layout, False)[0]
    newSource = rv.commands.addSourceVerbose([track], None)
    rv.commands.setNodeInputs(layout, stackInputs)
    rv.extra_commands.setUIName(
        rv.commands.nodeGroup(newSource), track
    )

    return newSource


def _ftrackCreateGroup(tracks, sourceNode, layout):
    singleSources = []
    for track in tracks:
        singleSources.append(
            rv.commands.nodeGroup(_ftrackAddVersion(track, layout))
        )

    rv.commands.setNodeInputs(
        sourceNode, singleSources
    )


def loadPlaylist(playlist, index=None, includeFrame=None):
    '''Load a playlist into RV.

    Load a specified *playlist* into RV and jump to an optional *index*. If
    *includeFrame* is an optional frame reference.

    '''
    _setWipeMode(False)
    startFrame = None

    if not includeFrame == 'false':
        startFrame = rv.extra_commands.sourceFrame(rv.commands.frame(), None)

    for oldSource in rv.commands.nodesOfType('RVSourceGroup'):
        rv.commands.deleteNode(oldSource)

    sources = []
    for item in playlist:
        sources.append(_getFilePath(
            item.get('componentId')
        ))

    sequenceSourceNode = _getSourceNode('sequence')

    _ftrackCreateGroup(sources, sequenceSourceNode, 'defaultLayout')
    rv.commands.setViewNode(sequenceSourceNode)

    if index:
        ftrackJumpTo(index, startFrame)


def validateComponentLocation(componentId, versionId):
    '''Return if the *componentId* is accessible in a local location.'''
    try:
        _getFilePath(componentId)
    except:
        logger.warning(
            'Component with Id "{0}" is not available in any location.'.format(
                componentId
            )
        )
        try:
            rv.commands.sendInternalEvent(
                'ftrack-event',
                base64.b64encode(
                    json.dumps(
                        {
                            'type': 'breakItem',
                            'versionId': versionId
                        }
                    )
                ),
                None
            )
        except:
            logger.exception(
                'Could not send internal event to ftrack.'
            )


def ftrackCompare(data):
    '''Activate compare mode in RV

    Activiate compare mode of *type* between *componentIdA* and *componentIdB*

    '''
    _setWipeMode(False)
    startFrame = None
    try:
        startFrame = rv.extra_commands.sourceFrame(rv.commands.frame(), None)
    except:
        pass

    componentIdA = data.get('componentIdA')
    componentIdB = data.get('componentIdB')
    mode = data.get('mode')

    trackA = _getFilePath(componentIdA)

    layout = 'defaultStack' if mode == 'wipe' else 'defaultLayout'

    if not mode == 'load':
        trackB = _getFilePath(componentIdB)

        try:
            if mode == 'wipe':
                sourceNode = _getSourceNode('stack')
                _ftrackCreateGroup([trackA, trackB], sourceNode, layout)
                rv.commands.setViewNode(sourceNode)
                rv.runtime.eval('rvui.toggleWipe()', ['rvui'])
            else:
                sourceNode = _getSourceNode('layout')
                _ftrackCreateGroup([trackA, trackB], sourceNode, layout)
                rv.commands.setViewNode(sourceNode)
        except:
            print traceback.format_exc()
    else:
        sourceNode = _getSourceNode('layout')
        _ftrackCreateGroup([trackA], sourceNode, layout)
        rv.commands.setViewNode(sourceNode)

    if startFrame > 1:
        rv.commands.setFrame(startFrame)


def _getEntityFromEnvironment():
    # Check for environment variable specifying additional information to
    # use when loading.
    eventEnvironmentVariable = 'FTRACK_CONNECT_EVENT'

    eventData = os.environ.get(eventEnvironmentVariable)
    if eventData is not None:
        try:
            decodedEventData = json.loads(base64.b64decode(eventData))
        except (TypeError, ValueError):
            logger.exception(
                'Failed to decode {0}: {1}'
                .format(eventEnvironmentVariable, eventData)
            )
        else:
            selection = decodedEventData.get('selection', [])

            # At present only a single entity which should represent an
            # ftrack List is supported.
            if selection:
                try:
                    entity = selection[0]
                    entityId = entity.get('entityId')
                    entityType = entity.get('entityType')
                    return entityId, entityType
                except (IndexError, AttributeError, KeyError):
                    logger.exception(
                        'Failed to extract selection information from: {0}'
                        .format(selection)
                    )
    else:
        logger.debug(
            'No event data retrieved. {0} not set.'
            .format(eventEnvironmentVariable)
        )

    return None, None


def getNavigationURL(params=None):
    '''Return URL to navigation panel based on *params*.'''
    return _generateURL(params, 'review_navigation')


def getActionURL(params=None):
    '''Return URL to action panel based on *params*.'''
    return _generateURL(params, 'review_action')


def _identify_entity_(entity_id):
    '''Identify provided *entity*.'''
    entity_types = [
        'Context',
        'AssetVersion',
        'FileComponent'
    ]

    entity = None
    for entity_type in entity_types:
        _entity = session.get(entity_type, entity_id)
        has_type = getattr(_entity, 'entity_type', None)
        if has_type:
            entity = _entity
            break

    return entity


def _generateURL(params=None, panelName=None):
    '''Return URL to panel in ftrack based on *params* or *panel*.'''
    entityId = None
    entityType = None

    url = ''
    if params:
        panelName = panelName or params

        try:
            params = json.loads(params)
            entityId = params['entityId'][0]
            entityType = params['entityType'][0]
        except Exception:
            entityId, entityType = _getEntityFromEnvironment()

        ftrack_entity = _identify_entity_(entityId)
        if not ftrack_entity:
                return

        try:
            url = session.get_widget_url(
                panelName, ftrack_entity, 'tf'
            )
        except Exception as exception:
            logger.exception(str(exception))

    logger.info('Returning url "{0}"'.format(url))

    return url


def ftrackFilePath(id):
    try:
        if id != "":
            filename = "%s.jpg" % id
            filepath = os.path.join(tempfile.gettempdir(), filename)
        else:
            filepath = tempfile.gettempdir()
        return filepath
    except:
        print traceback.format_exc()
        return ""


def ftrackUUID(short):
    '''Retun a uuid based on uuid1
    '''
    return str(uuid())


def ftrackJumpTo(index=0, startFrame=1):
    '''Move playhead to an index

    Moves the RV playhead to the specified *index*

    '''
    index = int(index)
    frameNumber = 0

    for idx, source in enumerate(rv.commands.nodesOfType('RVFileSource')):
        if not idx >= index:
            data = rv.commands.sourceMediaInfoList(source)[0]
            add = (data.get('endFrame', 0) - data.get('startFrame', 0)) + 1
            add = 1 if add == 0 else add
            frameNumber += (add)

    rv.commands.setFrame(frameNumber + startFrame)


def create_component(encoded_args):
    '''Create component without adding it to a location.

    *encoded_args* should be a JSON encoded dictionary containing file_name and
    frame.

    Store reference in annotation_components.
    '''
    args = json.loads(encoded_args)
    file_name = args['file_name']
    frame = args['frame']

    component_name = 'Frame_{0}'.format(frame)
    file_path = os.path.join(ftrackFilePath(''), file_name)
    logger.info(u'Creating component: {0!r}'.format(
        file_path
    ))

    component = session.create_component(
        component_name,
        path=file_path,
        location=None
    )
    component_id = component['id']
    annotation_components[component_id] = component
    return component_id


def upload_component(component_id):
    '''Add component with *component_id* to ftrack server location.'''
    logger.info(u'Adding component {0!r} to ftrack server location.'.format(
        component_id
    ))
    component = annotation_components[component_id]
    server_location = session.query('Location where name is "ftrack.server"')
    server_location.add_component(component)
    del annotation_components[component_id]
    return component_id
