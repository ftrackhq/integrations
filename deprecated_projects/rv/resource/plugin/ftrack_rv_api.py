# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import sys
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


ftrack_rv_logger_name = 'ftrack_rv'


try:
    import ftrack_logging

    ftrack_logging.configure_logging(ftrack_rv_logger_name)
    # Setup logging.
except Exception as error:
    logging.warning('Failed to Initialize logging.', error)

logger = logging.getLogger(ftrack_rv_logger_name)
logger.debug('PY3 Enabled: {}'.format(os.environ.get('RV_PYTHON3', 'NOT SET')))
logger.debug('Interpreter {}'.format(sys.executable))
logger.debug('version {}'.format(sys.version_info))
# Check whether the plugin is running from within connect or as standalone
# is_standalone = not bool(os.getenv('FTRACK_CONNECT_EVENT'))


# Check for base environment presence.
required_envs = ['FTRACK_SERVER', 'FTRACK_API_KEY']
for env in required_envs:
    if env not in os.environ:
        logger.error('{0} environment not found!'.format(env))


# Setup ssl certificate path.
cacert_path = os.path.join(os.path.dirname(__file__), 'cacert.pem')
os.environ['REQUESTS_CA_BUNDLE'] = cacert_path

# Setup dependencies path.
dependencies_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), 'dependencies.zip')
)

logger.debug('Adding {} to PATH'.format(dependencies_path))
sys.path.insert(0, dependencies_path)


# Try import ftrack's new API.
try:
    import ftrack_api
    from ftrack_api.symbol import ORIGIN_LOCATION_ID, SERVER_LOCATION_ID

except ImportError as e:
    logger.error('No Ftrack API module found in {}'.format(dependencies_path))
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


# Initialize New API
try:
    session = ftrack_api.Session(auto_connect_event_hub=False)

    # Get some useful locations.
    origin_location = session.get('Location', ORIGIN_LOCATION_ID)
    server_location = session.get('Location', SERVER_LOCATION_ID)

except Exception as e:
    logger.error(e)
    raise


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

            rv.extra_commands.setUIName(sequenceSourceNode, 'SequenceNode')

        return sequenceSourceNode

    elif nodeType == 'stack':
        if stackSourceNode is None:
            stackSourceNode = rv.commands.newNode('RVStackGroup', 'Stack')

            rv.extra_commands.setUIName(stackSourceNode, 'StackNode')

        return stackSourceNode

    elif nodeType == 'layout':
        if layoutSourceNode is None:
            layoutSourceNode = rv.commands.newNode('RVLayoutGroup', 'Layout')

            rv.extra_commands.setUIName(layoutSourceNode, 'LayoutNode')

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
        ftrack_component = session.get('Component', componentId)
        location = session.pick_location(component=ftrack_component)
        path = location.get_filesystem_path(ftrack_component)
        componentFilesystemPaths[componentId] = path

    return path


def _ftrackAddVersion(track, layout):
    stackInputs = rv.commands.nodeConnections(layout, False)[0]
    newSource = rv.commands.addSourceVerbose([track], None)
    rv.commands.setNodeInputs(layout, stackInputs)
    rv.extra_commands.setUIName(rv.commands.nodeGroup(newSource), track)

    return newSource


def _ftrackCreateGroup(tracks, sourceNode, layout):
    singleSources = []
    for track in tracks:
        try:
            singleSources.append(
                rv.commands.nodeGroup(_ftrackAddVersion(track, layout))
            )
        except Exception as error:
            logger.exception(error)

    rv.commands.setNodeInputs(sourceNode, singleSources)


def loadPlaylist(playlist, index=None, includeFrame=None):
    '''Load a playlist into RV.

    Load a specified *playlist* into RV and jump to an optional *index*. If
    *includeFrame* is an optional frame reference.

    '''
    _setWipeMode(False)
    startFrame = 1

    if not includeFrame == 'false':
        startFrame = rv.extra_commands.sourceFrame(rv.commands.frame(), None)

    for oldSource in rv.commands.nodesOfType('RVSourceGroup'):
        rv.commands.deleteNode(oldSource)

    sources = []
    for item in playlist:
        sources.append(_getFilePath(item.get('componentId')))

    sequenceSourceNode = _getSourceNode('sequence')

    _ftrackCreateGroup(sources, sequenceSourceNode, 'defaultLayout')
    rv.commands.setViewNode(sequenceSourceNode)

    if index:
        ftrackJumpTo(index, startFrame)


def validateComponentLocation(componentId, versionId):
    '''Return if the *componentId* is accessible in a local location.'''
    try:
        _getFilePath(componentId)
    except Exception:
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
                        {'type': 'breakItem', 'versionId': versionId}
                    ).encode("utf-8")
                ).decode('ascii'),
                None,
            )
        except Exception:
            logger.error('Could not send internal event to ftrack.')


def ftrackCompare(data):
    '''Activate compare mode in RV

    Activiate compare mode of *type* between *componentIdA* and *componentIdB*

    '''
    _setWipeMode(False)
    startFrame = 1
    try:
        startFrame = rv.extra_commands.sourceFrame(rv.commands.frame(), None)
    except Exception:
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
        except Exception:
            print(traceback.format_exc())
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
            logger.error(
                'Failed to decode {0}: {1}'.format(
                    eventEnvironmentVariable, eventData
                )
            )
        else:
            selection = decodedEventData.get('selection', [])
            logger.info('selection {}'.format(selection))
            # At present only a single entity which should represent an
            # ftrack List is supported.
            if selection:
                try:
                    entity = selection[0]
                    entityId = entity.get('entityId')
                    entityType = entity.get('entityType')
                    return entityId, entityType
                except (IndexError, AttributeError, KeyError):
                    logger.error(
                        'Failed to extract selection information from: {0}'.format(
                            selection
                        )
                    )
    else:
        logger.debug(
            'No event data retrieved. {0} not set.'.format(
                eventEnvironmentVariable
            )
        )

    return None, None


def getNavigationURL(params=None):
    '''Return URL to navigation panel based on *params*.'''
    return _generateURL(params, 'review_navigation')


def getActionURL(params=None):
    '''Return URL to action panel based on *params*.'''
    return _generateURL(params, 'review_action')


def _translateEntityType(entityType):
    '''Return translated entity type tht can be used with API.'''
    # Get entity type and make sure it is lower cased. Most places except
    # the component tab in the Sidebar will use lower case notation.
    entity_type = entityType.replace('_', '').lower()

    for schema in session.schemas:
        alias_for = schema.get('alias_for')

        if (
            alias_for
            and isinstance(alias_for, str)
            and alias_for.lower() == entity_type
        ):
            return schema['id']

    for schema in session.schemas:
        if schema['id'].lower() == entity_type:
            return schema['id']

    raise ValueError(
        'Unable to translate entity type: {0}.'.format(entity_type)
    )


def _get_temp_data_url(name, temp_data_id):
    operation = {
        'action': 'get_widget_url',
        'name': name,
        'theme': None,
    }

    result = session.call([operation])
    url = result[0]['widget_url']
    full_url = '{}&entityType=tempdata&entityId={}'.format(url, temp_data_id)
    return full_url


def _generateURL(params=None, panelName=None):
    '''Return URL to panel in ftrack based on *params* or *panel*.'''
    logger.info('_generateURL with params: {}'.format(params))
    url = ''
    try:
        entityId = None
        entityType = None

        if params:
            panelName = panelName or params
            try:
                params = json.loads(params)
                entityId = params['entityId'][0]
                entityType = params['entityType'][0]
            except Exception:
                entityId, entityType = _getEntityFromEnvironment()

            if entityId and entityType:
                if entityType != 'tempdata':
                    new_entity_type = _translateEntityType(entityType)
                    new_entity = session.get(new_entity_type, entityId)
                    try:
                        url = session.get_widget_url(
                            panelName, entity=new_entity
                        )
                    except Exception as exception:
                        logger.error(str(exception))
                else:
                    try:
                        url = _get_temp_data_url(panelName, entityId)
                    except Exception as exception:
                        logger.error(str(exception))

        logger.info('Returning url "{0}"'.format(url))
    except Exception as error:
        logger.exception('Failed to generate URL. {}'.format(error))
    return url


def ftrackFilePath(id):
    try:
        if id != "":
            filename = "%s.jpg" % id
            filepath = os.path.join(tempfile.gettempdir(), filename)
        else:
            filepath = tempfile.gettempdir()
        return filepath
    except Exception:
        logger.exception('Failed to get file path.')
        return ''


def ftrackUUID(short):
    '''Retun a uuid based on uuid1'''
    return str(uuid())


def ftrackJumpTo(index=0, startFrame=1):
    '''Move playhead to an index

    Moves the RV playhead to the specified *index*

    '''
    try:
        index = int(index)
        frameNumber = 0

        for idx, source in enumerate(rv.commands.nodesOfType('RVFileSource')):
            if not idx >= index:
                data = rv.commands.sourceMediaInfoList(source)[0]
                add = (data.get('endFrame', 0) - data.get('startFrame', 0)) + 1
                add = 1 if add == 0 else add
                frameNumber += add

        rv.commands.setFrame(frameNumber + startFrame)
    except Exception:
        logger.exception('Failed to jump to index.')


def create_component(encoded_args):
    '''Create component without adding it to a location.

    *encoded_args* should be a JSON encoded dictionary containing file_name and
    frame.

    Store reference in annotation_components.
    '''
    component_id = None
    try:
        args = json.loads(encoded_args)
        file_name = args['file_name']
        frame = args['frame']

        component_name = 'Frame_{0}'.format(frame)
        file_path = os.path.join(ftrackFilePath(''), file_name)
        logger.info(u'Creating component: {0!r}'.format(file_path))
        component = session.create_component(
            path=file_path, data=dict(name=component_name), location=None
        )
        component_id = component['id']
        annotation_components[component_id] = component
    except Exception:
        logger.exception('Failed to create component.')

    return component_id


def upload_component(component_id):
    '''Add component with *component_id* to ftrack server location.'''
    try:
        logger.info(
            u'Adding component {0!r} to ftrack server location.'.format(
                component_id
            )
        )
        component = annotation_components[component_id]
        server_location.add_component(component, origin_location)
        del annotation_components[component_id]
    except Exception:
        logger.exception('Failed to upload component')
    else:
        return component_id
