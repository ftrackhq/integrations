import sys
import json
import re
import tempfile
import base64
import traceback
import os
from uuid import uuid1 as uuid
import logging
import platform
import base64

from PySide2 import QtCore
from PySide2 import QtGui
from PySide2 import QtWidgets
from PySide2 import QtWebEngineWidgets
from PySide2.QtCore import SIGNAL, SLOT


# setup logging
from ftrack_logging import configure_logging

configure_logging('ftrack-rv')
logger = logging.getLogger('ftrack-rv')

# Setup dependencies path.
dependencies_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), 'dependencies.zip')
)

logger.debug('Adding {} to PATH'.format(dependencies_path))
sys.path.insert(0, dependencies_path)


try:
    import ftrack_api
    from ftrack_api.symbol import ORIGIN_LOCATION_ID, SERVER_LOCATION_ID
except ImportError as error:
    raise ImportError('Could not import ftrack api, aborting.')

# import RV related modules
import rv
from rv import rvtypes as rvt
from rv import commands as rvc
from rv import extra_commands as rve
from rv import qtutils as rvq
from rv import rvui
from pymu import MuSymbol
from rv.commands import NeutralMenuState


class FtrackMode(rv.rvtypes.MinorMode):
    "A simple example that shows how to make shift-Z start/stop playback"

    def __init__(self, name):
        logger.debug('init')
        rv.rvtypes.MinorMode.__init__(self)

        self._name = name

        self.setup_variables()
        self.check_envs()
        self.create_session()
        self.create_bindings()

    @property
    def name(self):
        return self._name

    @property
    def session(self):
        return self._session

    def togglePlayback(self, event):
        if rvc.isPlaying():
            rvc.stop()
        else:
            rvc.play()

    def create_session(self):
        self._session = ftrack_api.Session(auto_connect_event_hub=False)

        # Get some useful locations.
        self.origin_location = self._session.get(
            'Location', ORIGIN_LOCATION_ID
        )
        self.server_location = self._session.get(
            'Location', SERVER_LOCATION_ID
        )
        logger.debug(self._session)

    def check_envs(self):
        logger.debug('check_envs')
        commandline_url = rvc.commandLineFlag('ftrackUrl', None)

        logger.debug(f'command line url {commandline_url}')
        if not commandline_url:
            # Check for base environment presence.
            required_envs = ['FTRACK_SERVER', 'FTRACK_API_KEY']
            for env in required_envs:
                if env not in os.environ:
                    logger.error('{0} environment not found!'.format(env))
        else:
            os.environ['FTRACK_SERVER'] = commandline_url

        # Setup ssl certificate path.
        cacert_path = os.path.join(os.path.dirname(__file__), 'cacert.pem')
        os.environ['REQUESTS_CA_BUNDLE'] = cacert_path

        logger.info(f'env FTRACK_SERVER: {os.getenv("FTRACK_SERVER")}')
        logger.info(f'env FTRACK_API_KEY: {os.getenv("FTRACK_API_KEY")}')
        logger.info(
            f'env REQUESTS_CA_BUNDLE: {os.getenv("REQUESTS_CA_BUNDLE")}'
        )

    def createActionWindow(self, data):
        logger.debug('createActionWindow')

        title = ''
        startSize = 500
        showTitle = False
        if self._dockActionWidget:
            return

        url = self._generateURL(
            rvc.commandLineFlag("params", None), "review_action"
        )
        self._dockActionWidget = QtWidgets.QDockWidget(
            title, self.mainWindow, QtCore.Qt.Widget
        )

        self._baseActionWidget = self.makeit()

        self._webActionWidget = self._baseActionWidget.findChild(
            QtCore.QObject, self.name
        )
        self._webNavigationWidget.loadFinished.connect(
            lambda: self.viewLoaded(
                self._baseActionWidget,
            )
        )

        self._webActionWidget.load(QtCore.QUrl(url))
        rvq.javascriptExport(self._webActionWidget.page())
        self._dockActionWidget.setWidget(self._baseActionWidget)

        self._titleActionWidget = self._dockActionWidget.titleBarWidget()

        if not showTitle:
            self._dockActionWidget.setTitleBarWidget(
                QtWidgets.QWidget(self.mainWindow)
            )

        self._dockActionWidget.topLevelChanged.connect(
            lambda: self.toggleTitleBar(
                self._dockActionWidget, self._titleActionWidget, False
            )
        )

        self._dockActionWidget.setFeatures(
            QtWidgets.QDockWidget.DockWidgetFloatable
            | QtWidgets.QDockWidget.DockWidgetMovable
        )

        self.mainWindow.addDockWidget(
            QtCore.Qt.RightDockWidgetArea, self._dockActionWidget
        )

        self._baseActionWidget.setMaximumWidth(startSize)
        self._baseActionWidget.setMinimumWidth(startSize)

        self._baseActionWidget.show()
        self._dockActionWidget.show()

    def makeit(self):
        logger.debug('makeit')

        form = QtWidgets.QWidget(self.mainWindow, QtCore.Qt.Widget)
        verticalLayout = QtWidgets.QVBoxLayout(form)
        verticalLayout.setSpacing(0)
        verticalLayout.setContentsMargins(4, 4, 4, 4)
        verticalLayout.setObjectName("verticalLayout")

        webView = QtWebEngineWidgets.QWebEngineView(form)
        webView.setObjectName(self.name)
        verticalLayout.addWidget(webView)
        return form

    def toggleFloating(self, event):
        logger.debug('toggleFloating')

        index = int(event.contents())

        dockWidget = QtWidgets.QDockWidget()
        titleWidget = QtWidgets.QWidget()

        if index == 3:
            dockWidget = self._dockNavigationWidget
            titleWidget = self._titleNavigationWidget

        else:
            dockWidget = self._dockActionWidget
            titleWidget = self._titleActionWidget

        if dockWidget.isFloating():
            dockWidget.setFloating(False)

        else:
            dockWidget.setFloating(True)

        self.toggleTitleBar(dockWidget, titleWidget, True)

    def shutdown(self, event):
        logger.debug('shutdown')
        event.reject()

        if self._webNavigationWidget:
            self._webNavigationWidget.page().setHtml("", QtCore.QUrl())

        if self._webActionWidget:
            self._webActionWidget.page().setHtml("", QtCore.QUrl())

    def ftrackEvent(self, event):
        content = base64.b64decode(event.contents())

        logger.debug(f'ftrackEvent {content}')
        try:
            self._webNavigationWidget.page().runJavaScript(
                "FT.updateFtrack(\"" + event.contents() + "\")"
            )
        except Exception as e:
            logger.error(e)

        try:
            self._webActionWidget.page().runJavaScript(
                "FT.updateFtrack(\"" + event.contents() + "\")"
            )
        except Exception as e:
            logger.error(e)

    def toggleTitleBar(self, dockWidget, titleWidget, ok):
        logger.debug('toggleTitleBar')

        if not dockWidget.isFloating():
            dockWidget.setTitleBarWidget(QtWidgets.QWidget(self.mainWindow))

        else:
            dockWidget.setTitleBarWidget(QtWidgets.QWidget(titleWidget))

    def viewLoaded(self, view):
        logger.debug('viewLoaded')

        view.setMaximumWidth(16777215)
        view.setMinimumWidth(0)
        view.setMaximumHeight(16777215)
        view.setMinimumHeight(250)

    def initUi(self):
        if not self._firstRender:
            return

        logger.debug('initUI')

        self._firstRender = False
        showTitle = False
        startSize = 500

        params = rvc.commandLineFlag("params", None)
        url = self._generateURL(params, 'review_navigation')

        if not url:
            noServer = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "SupportFiles",
                'noserver.html',
            )
            urlPrefix = (
                "file:///" if (platform.system() == "Windows") else "file://"
            )
            url = ''.join([urlPrefix, noServer]).encode('utf-8')

        logger.info(f'url: {url}')

        title = ''
        self._dockNavigationWidget = QtWidgets.QDockWidget(
            title, self.mainWindow, QtCore.Qt.Widget
        )

        self._baseNavigationWidget = self.makeit()
        self._webNavigationWidget = self._baseNavigationWidget.findChild(
            QtCore.QObject, self.name
        )

        self._webNavigationWidget.loadFinished.connect(
            lambda: self.viewLoaded(self._baseNavigationWidget)
        )

        self._webNavigationWidget.load(QtCore.QUrl(str(url)))
        rvq.javascriptExport(self._webNavigationWidget.page())
        self._dockNavigationWidget.setWidget(self._baseNavigationWidget)

        self._titleNavigationWidget = (
            self._dockNavigationWidget.titleBarWidget()
        )

        if not showTitle:
            self._dockNavigationWidget.setTitleBarWidget(
                QtWidgets.QWidget(self.mainWindow)
            )

        self._dockNavigationWidget.topLevelChanged.connect(
            lambda: self.toggleTitleBar(
                self._dockNavigationWidget, self._titleNavigationWidget, False
            )
        )

        self._dockNavigationWidget.setFeatures(
            QtWidgets.QDockWidget.DockWidgetFloatable
            | QtWidgets.QDockWidget.DockWidgetMovable
        )

        self.mainWindow.addDockWidget(
            QtCore.Qt.BottomDockWidgetArea, self._dockNavigationWidget
        )

        self._baseNavigationWidget.setMaximumHeight(startSize)
        self._baseNavigationWidget.setMinimumHeight(startSize)

        self._baseNavigationWidget.show()
        self._dockNavigationWidget.show()

        self.mainWindow.show()

    def frameChanged(self, event):
        logger.debug(f'FrameChanged {event}')
        source = int(
            re.smatch(
                "[a-zA-Z]+([0-9]+)", rvc.sourcesAtFrame(rvc.frame())[0]
            ).back()
        )
        if self._currentSource != source:
            _currentSource = source
            data_string = (
                "{\"type\":\"changedGroup\",\"index\":\""
                + _currentSource
                + "\"}"
            )
            data = data_string.encode('utf-8')
            data = base64.b64encode(data)
            logger.debug(data)
            self._webNavigationWidget.page().runJavaScript(
                "FT.updateFtrack(\""
                + data.encode('latin-1').decode('utf-8')
                + "\")"
            )

    def navGroupChanged(self, event):
        logger.debug(f'navGroupChanged {event}')
        self.setViewNode("sourceGroup00000" + event.contents())

    def ftrackToggle(self, event):
        logger.debug(f'ftrackToggle {event}')

        if self._isHidden:
            self._isHidden = False
            self.showPanels()
            self.initUi()
        else:
            self._isHidden = True
            self.hidePanels()

    def hidePanels(self):
        logger.debug(f'hidePanels')

        if self._baseNavigationWidget:
            self._baseNavigationWidget.hide()
        if self._dockNavigationWidget:
            self._dockNavigationWidget.hide()
        if self._baseActionWidget:
            self._baseActionWidget.hide()
        if self._dockActionWidget:
            self._dockActionWidget.hide()

    def showPanels(self):
        logger.debug(f'hidePanels')

        if self._baseNavigationWidget:
            self._baseNavigationWidget.show()
        if self._dockNavigationWidget:
            self._dockNavigationWidget.show()

        if self._baseActionWidget:
            self._baseActionWidget.show()
        if self._dockActionWidget:
            self._dockActionWidget.show()

    def showPanelsOnStartupToggle(self, event):
        logger.debug(f'showPanelsOnStartupToggle')

        if not self._showPanelsOnStartup:
            rvc.writeSettings("ftrack", "showPanelsOnStartUp", True)
            self._showPanelsOnStartup = True
            logger.debug("show on startup: %s" % self._showPanelsOnStartup)

        else:
            rvc.writeSettings("ftrack", "showPanelsOnStartUp", False)
            self._showPanelsOnStartup = False
            logger.debug("show on startup: %s" % self._showPanelsOnStartup)

    def panelState(self):
        logger.debug("panelState: %s" % self._isHidden)
        return (
            rvc.CheckedMenuState if self._isHidden else rvc.UncheckedMenuState
        )

    def debugPrintState(self):
        logger.debug("debugPrintState: %s" % self._debug)
        return rvc.CheckedMenuState if self._debug else rvc.UncheckedMenuState

    def showPanelsOnStartupState(self):
        logger.debug("show on startup: %s" % self._showPanelsOnStartup)
        return (
            rvc.CheckedMenuState
            if self._showPanelsOnStartup
            else rvc.UncheckedMenuState
        )

    def debugToggle(self, event):
        logger.debug('debugToggle')
        if self._debug:
            self._debug = False
            rvc.writeSettings("ftrack", "debug", False)

        else:
            self._debug = True
            rvc.writeSettings("ftrack", "debug", True)

        logger.debug("Debug print: " + str(self._debug))

    def create_bindings(self):
        logger.debug('create_bindings')

        self._showPanelsOnStartup = rvc.readSettings(
            "ftrackMode", "showPanelsOnStartUp", True
        )
        self._debug = rvc.readSettings("ftrackMode", "debug", False)

        rvc.bind(
            "default",
            "global",
            "ftrack-event",
            self.ftrackEvent,
            "Update action window",
        )
        rvc.bind(
            "default",
            "global",
            "ftrack-timeline-loaded",
            self.createActionWindow,
            "User is logged in, create action window",
        )

        rvc.bind(
            "default",
            "global",
            "ftrack-toggle-floating",
            self.toggleFloating,
            "Toggle floating panel",
        )
        rvc.bind(
            "default",
            "global",
            "frame-changed",
            self.frameChanged,
            "New frame",
        )
        rvc.bind(
            "default",
            "global",
            "ftrack-changed-group",
            self.navGroupChanged,
            "New group selected",
        )

        # rvc.bind("default", "global","ftrack-upload-frame", self.ftrackExportAll, "Upload frame to FTrack")
        # rvc.bind("default", "global","ftrack-upload-frames", self.ftrackExportAll, "Upload all annotated frames to FTrack")

        menu = [
            (
                "ftrackReview",
                [
                    (
                        "Toggle panels",
                        self.ftrackToggle,
                        "control shift t",
                        lambda: NeutralMenuState,
                    ),
                    (
                        "Preferences",
                        [
                            (
                                "Show panels on startup",
                                self.showPanelsOnStartupToggle,
                                "",
                                self.showPanelsOnStartupState,
                            ),
                            (
                                "Debug print",
                                self.debugToggle,
                                "control shift d",
                                self.debugPrintState,
                            ),
                        ],
                    ),
                ],
            )
        ]

        self.init(
            self.name,
            [("before-session-deletion", self.shutdown, "")],
            None,
            menu,
        )

        rvc.sendInternalEvent("key-down--`")

        rvc.bind(
            "default",
            "global",
            "key-down--control--T",
            self.ftrackToggle,
            "Toggle ftrackReview panels",
        )
        rvc.bind(
            "default",
            "global",
            "key-down--control--D",
            self.debugToggle,
            "Toggle ftrackReview debug prints",
        )

        if self._showPanelsOnStartup:
            self._isHidden = False
            self.initUi()

        else:
            self._isHidden = True

    def setup_variables(self):
        # Cache to keep track of filesystem path for components.
        # This will cause the component to use the same filesystem path
        # during the entire session.
        logger.debug('setup_variables')
        self.mainWindow = rvq.sessionWindow()
        self._firstRender = True
        self._isHidden = False
        self._debug = False

        self._dockActionWidget = None
        self._webActionWidget = None

        self._currentSource = 1
        self.componentFilesystemPaths = {}

        self.sequenceSourceNode = None
        self.stackSourceNode = None
        self.layoutSourceNode = None

        # Store references to annotation components being uploaded between methods.
        self.annotation_components = {}
        self.globalBindings = None  # [("Event-Name", self.eventCallback, "DescriptionOfBinding")]
        self.localBindings = None

        self._showPanelsOnStartup = False

    def createMode():
        "Required to initialize the module. RV will call this function to create your mode."
        return FtrackMode('webview')

    # TODO , this is not finished yet, do not enable
    def ftrackExportAll(self, event):
        _token = event.contents()
        # Add all the frames and export
        # Generate filenames that are unique
        # set name eg. Frame_159_1.jpg,Frame_159_2.jpg

        _filePath = self.getFilePath("")
        tmpUpload = []
        _uuid = self.ftrackUUID()

        # // Get all the annotated frames
        # // Function
        frames = []

        if event.name() == "ftrack-upload-frame":
            frames.push_back(rvui.frame())

        else:
            frames = self.findAnnotatedFrames()

        self._annotatedFrames = frames

        for i in frames:
            f = frames[i]
            fpadd = "%04d" % f
            tmpUpload.append("%s_%s.jpg" % (_uuid, fpadd))

        self._doUpload = tmpUpload
        # args = [
        #     rv.makeTempSession(),
        #     "-o", "%s/%s_#.jpg" % (_filePath,_uuid),
        #     "-t", str(timestr),
        #     "-overlay","frameburn","0.8","1.0","30.0"
        # ]

        # self.uploadingCount(self._doUpload.size())
        # if (self._doUpload.size() > 0):
        #     rvc.rvio("Export Annotated Frames", args, self.uploadAll);

    def uploadAll(self):
        logger.debug('Upload all frames')
        for i in self._doUpload:
            self.upload_annotation(self._doUpload[i], self._annotatedFrames[i])

    def uploadingCount(self, count):
        data_string = "{\"type\":\"uploadCount\",\"count\":\"" + count + "\"}"
        data = data_string.encode('utf-8')
        data = base64.b64encode(data)
        self._webActionWidget.page().runJavaScript(
            "FT.updateFtrack(\""
            + data.encode('latin-1').decode('utf-8')
            + "\")"
        )

    # ----------------------------------- CODE FROM OLD ftrack_rv_api --------------------------------------------------

    def _getFilePath(self, componentId):
        '''Return a single access path based on *source* and *location*'''

        path = self.componentFilesystemPaths.get(componentId, None)

        if path is None:
            ftrack_component = self.session.get('Component', componentId)
            location = self.session.pick_location(component=ftrack_component)
            path = location.get_filesystem_path(ftrack_component)
            self.componentFilesystemPaths[componentId] = path

        return path

    def _setWipeMode(self, state):
        '''Util to set the state of wipes instead of toggle.'''
        if (
            rv.runtime.eval('rvui.wipeShown()', ['rvui']) != -1
            and state is False
        ):
            rv.runtime.eval('rvui.toggleWipe()', ['rvui'])

        if (
            rv.runtime.eval('rvui.wipeShown()', ['rvui']) == -1
            and state is True
        ):
            rv.runtime.eval('rvui.toggleWipe()', ['rvui'])

    def _getSourceNode(self, nodeType='sequence'):
        '''Return source node of *nodeType*.'''

        if nodeType == 'sequence':
            if self.sequenceSourceNode is None:
                self.sequenceSourceNode = rvc.newNode(
                    'RVSequenceGroup', 'Sequence'
                )

                rv.extra_commands.setUIName(
                    self.sequenceSourceNode, 'SequenceNode'
                )

            return self.sequenceSourceNode

        elif nodeType == 'stack':
            if stackSourceNode is None:
                stackSourceNode = rvc.newNode('RVStackGroup', 'Stack')

                rv.extra_commands.setUIName(stackSourceNode, 'StackNode')

            return stackSourceNode

        elif nodeType == 'layout':
            if layoutSourceNode is None:
                layoutSourceNode = rvc.newNode('RVLayoutGroup', 'Layout')

                rv.extra_commands.setUIName(layoutSourceNode, 'LayoutNode')

            return layoutSourceNode

    def _ftrackAddVersion(track, layout):
        stackInputs = rvc.nodeConnections(layout, False)[0]
        newSource = rvc.addSourceVerbose([track], None)
        rvc.setNodeInputs(layout, stackInputs)
        rve.setUIName(rvc.nodeGroup(newSource), track)

        return newSource

    def _ftrackCreateGroup(self, tracks, sourceNode, layout):
        singleSources = []
        for track in tracks:
            try:
                singleSources.append(
                    rvc.nodeGroup(self._ftrackAddVersion(track, layout))
                )
            except Exception as error:
                logger.exception(error)

        rvc.setNodeInputs(sourceNode, singleSources)

    def loadPlaylist(self, playlist, index=None, includeFrame=None):
        '''Load a playlist into RV.

        Load a specified *playlist* into RV and jump to an optional *index*. If
        *includeFrame* is an optional frame reference.

        '''
        logger.debug('LoadPlaylist')
        self._setWipeMode(False)
        startFrame = 1

        if not includeFrame == 'false':
            startFrame = rve.sourceFrame(rvc.frame(), None)

        for oldSource in rvc.nodesOfType('RVSourceGroup'):
            rvc.deleteNode(oldSource)

        sources = []
        for item in playlist:
            sources.append(self._getFilePath(item.get('componentId')))

        sequenceSourceNode = self._getSourceNode('sequence')

        self._ftrackCreateGroup(sources, sequenceSourceNode, 'defaultLayout')
        rvc.setViewNode(sequenceSourceNode)

        if index:
            self.ftrackJumpTo(index, startFrame)

    def validateComponentLocation(self, componentId, versionId):
        '''Return if the *componentId* is accessible in a local location.'''
        try:
            self._getFilePath(componentId)
        except Exception:
            logger.debug(
                'Component with Id "{0}" is not available in any location.'.format(
                    componentId
                )
            )
            try:
                rvc.sendInternalEvent(
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

    def ftrackCompare(self, data):
        '''Activate compare mode in RV

        Activiate compare mode of *type* between *componentIdA* and *componentIdB*

        '''
        self._setWipeMode(False)
        startFrame = 1
        try:
            startFrame = rve.sourceFrame(rvc.frame(), None)
        except Exception:
            pass

        componentIdA = data.get('componentIdA')
        componentIdB = data.get('componentIdB')
        mode = data.get('mode')

        trackA = self._getFilePath(componentIdA)

        layout = 'defaultStack' if mode == 'wipe' else 'defaultLayout'

        if not mode == 'load':
            trackB = self._getFilePath(componentIdB)

            try:
                if mode == 'wipe':
                    sourceNode = self._getSourceNode('stack')
                    self._ftrackCreateGroup(
                        [trackA, trackB], sourceNode, layout
                    )
                    rvc.setViewNode(sourceNode)
                    rv.runtime.eval('rvui.toggleWipe()', ['rvui'])
                else:
                    sourceNode = self._getSourceNode('layout')
                    self._ftrackCreateGroup(
                        [trackA, trackB], sourceNode, layout
                    )
                    rvc.setViewNode(sourceNode)
            except Exception:
                print(traceback.format_exc())
        else:
            sourceNode = self._getSourceNode('layout')
            self._ftrackCreateGroup([trackA], sourceNode, layout)
            rvc.setViewNode(sourceNode)

        if startFrame > 1:
            rvc.setFrame(startFrame)

    def _getEntityFromEnvironment(self):
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

    def getNavigationURL(self, params=None):
        '''Return URL to navigation panel based on *params*.'''
        return self._generateURL(params, 'review_navigation')

    def getActionURL(self, params=None):
        '''Return URL to action panel based on *params*.'''
        return self._generateURL(params, 'review_action')

    def _translateEntityType(self, entityType):
        '''Return translated entity type tht can be used with API.'''
        # Get entity type and make sure it is lower cased. Most places except
        # the component tab in the Sidebar will use lower case notation.
        entity_type = entityType.replace('_', '').lower()

        for schema in self.session.schemas:
            alias_for = schema.get('alias_for')

            if (
                alias_for
                and isinstance(alias_for, str)
                and alias_for.lower() == entity_type
            ):
                return schema['id']

        for schema in self.session.schemas:
            if schema['id'].lower() == entity_type:
                return schema['id']

        raise ValueError(
            'Unable to translate entity type: {0}.'.format(entity_type)
        )

    def _get_temp_data_url(self, name, temp_data_id):
        logger.debug(f'_get_temp_data_url: {name} {temp_data_id}')

        operation = {
            'action': 'get_widget_url',
            'name': name,
            'theme': None,
        }

        result = self.session.call([operation])
        url = result[0]['widget_url']
        full_url = '{}&entityType=tempdata&entityId={}'.format(
            url, temp_data_id
        )
        return full_url

    # CURRENT ERROR IN DECODING PARAMS
    def _generateURL(self, params, panelName=None):
        '''Return URL to panel in ftrack based on *params* or *panel*.'''
        logger.debug(f'_generateURL with params: {params}')
        url = ''

        try:
            entityId = None
            entityType = None

            if params:
                panelName = panelName or params
                try:
                    params = json.loads(params)
                    print(f'params : {params} , {type(params)}')
                    entityId = params['entityId'][0]
                    entityType = params['entityType'][0]

                except Exception as e:
                    logger.error(e)
                    print(e)
                    entityId, entityType = self._getEntityFromEnvironment()

                print(f'entityId:  {entityId}')
                print(f'entityType:  {entityType}')

                if entityId and entityType:
                    if entityType != 'tempdata':
                        new_entity_type = self._translateEntityType(entityType)
                        new_entity = self.session.get(
                            new_entity_type, entityId
                        )
                        try:
                            url = self.session.get_widget_url(
                                panelName, entity=new_entity
                            )
                        except Exception as exception:
                            logger.error(str(exception))
                    else:
                        try:
                            url = self._get_temp_data_url(panelName, entityId)
                        except Exception as exception:
                            logger.error(str(exception))

        except Exception as error:
            logger.exception('Failed to generate URL. {}'.format(error))

        logger.info('Returning url "{0}"'.format(url))
        return url

    def ftrackFilePath(self, id):
        logger.debug(f'ftrackFilePath {id}')

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

    def ftrackUUID(self, short):
        '''Retun a uuid based on uuid1'''
        logger.debug(f'ftrackUUID {short}')

        return str(uuid())

    def ftrackJumpTo(self, index=0, startFrame=1):
        '''Move playhead to an index

        Moves the RV playhead to the specified *index*

        '''
        logger.debug(f'ftrackJumpTo {index} {startFrame}')

        try:
            index = int(index)
            frameNumber = 0

            for idx, source in enumerate(rvc.nodesOfType('RVFileSource')):
                if not idx >= index:
                    data = rvc.sourceMediaInfoList(source)[0]
                    add = (
                        data.get('endFrame', 0) - data.get('startFrame', 0)
                    ) + 1
                    add = 1 if add == 0 else add
                    frameNumber += add

            rvc.setFrame(frameNumber + startFrame)
        except Exception:
            logger.exception('Failed to jump to index.')

    def create_component(self, encoded_args):
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
            file_path = os.path.join(self.ftrackFilePath(''), file_name)
            logger.info(u'Creating component: {0!r}'.format(file_path))
            component = self.session.create_component(
                path=file_path, data=dict(name=component_name), location=None
            )
            component_id = component['id']
            self.annotation_components[component_id] = component
        except Exception:
            logger.exception('Failed to create component.')

        return component_id

    def upload_component(self, component_id):
        '''Add component with *component_id* to ftrack server location.'''
        try:
            logger.info(
                u'Adding component {0!r} to ftrack server location.'.format(
                    component_id
                )
            )
            component = self.annotation_components[component_id]
            self.server_location.add_component(component, self.origin_location)
            del self.annotation_components[component_id]
        except Exception:
            logger.exception('Failed to upload component')
        else:
            return component_id


def createMode():
    return FtrackMode('webview')


def theMode():
    m = rvui.minorModeFromName('webview')
    return m
