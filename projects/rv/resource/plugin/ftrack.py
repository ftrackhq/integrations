import sys
import json
import re
import tempfile
import base64
import time
import traceback
import os
from uuid import uuid1 as uuid
import logging
import platform
import base64
import subprocess
from distutils.spawn import find_executable

from PySide2 import QtCore
from PySide2 import QtGui
from PySide2 import QtWidgets
from PySide2 import QtWebEngineWidgets
from PySide2.QtCore import SIGNAL, SLOT


# setup logging
from ftrack_logging import configure_logging

configure_logging('ftrack_rv')
logger = logging.getLogger('ftrack_rv')

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

# import ftack_rv_api
import ftrack_rv_api as fra

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

        url = fra._generateURL(
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

        jsContent = f'FT.updateFtrack("{event.contents()}")'
        logger.debug(jsContent)

        try:
            self._webNavigationWidget.page().runJavaScript(jsContent)
        except Exception as e:
            logger.error(e)

        try:
            self._webActionWidget.page().runJavaScript(jsContent)
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
        url = fra._generateURL(params, 'review_navigation')

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
        logger.debug(f'FrameChanged | evt : {event}')

        frame = rvc.sourcesAtFrame(rvc.frame())[0]
        source = int(re.match("[a-zA-Z]+([0-9]+)", frame).group(1))
        logger.debug(
            f'FrameChanged | _currentSource : {self._currentSource} , source {source}'
        )

        if self._currentSource != source:
            _currentSource = source

            data = base64.b64encode(
                json.dumps(
                    {'type': 'changedGroup', 'index': str(_currentSource)}
                ).encode("utf-8")
            ).decode('ascii')

            logger.debug(data)
            jsData = f'FT.updateFtrack("{data}")'
            self._webNavigationWidget.page().runJavaScript(jsData)

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

        rvc.bind(
            "default",
            "global",
            "ftrack-upload-frame",
            self.ftrackExportAll,
            "Upload frame to FTrack",
        )

        rvc.bind(
            "default",
            "global",
            "ftrack-upload-frames",
            self.ftrackExportAll,
            "Upload all annotated frames to FTrack",
        )

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

        # rvc.sendInternalEvent("key-down--`")

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

        self.sequenceSourceNode = None
        self.stackSourceNode = None
        self.layoutSourceNode = None

        self.globalBindings = None  # [("Event-Name", self.eventCallback, "DescriptionOfBinding")]
        self.localBindings = None

        self._showPanelsOnStartup = False

    def createMode():
        "Required to initialize the module. RV will call this function to create your mode."
        return FtrackMode('webview')

    def uploadAll(self):
        logger.debug('Upload all frames')
        for i in self._doUpload:
            self.upload_annotation(self._doUpload[i], self._annotatedFrames[i])

    def uploadingCount(self, count):
        logger.debug(f'uploadingCount: {count}')

        data = base64.b64encode(
            json.dumps({'type': 'uploadCount', 'count': count}).encode("utf-8")
        ).decode('ascii')

        self._webActionWidget.page().runJavaScript(
            f'FT.updateFtrack("{data}")'
        )

    def upload_annotation(self, filename, frame):
        '''
        Upload a single annotation saved as *filename*.

        Creates a component, adds the component to the note form and then
        adds the component to the ftrack.server location.
        '''
        logger.debug(f'uploading file : {filename}')

        encoded_args = json.dumps({'file_name': filename, 'frame': frame})

        component_id = fra.create_component(encoded_args)
        logger.debug(f'created component : {component_id}')
        self.on_upload_started(component_id)

        fra.upload_component(component_id)
        logger.debug(f'Upload completed')
        self.on_upload_complete(component_id)

    def on_upload_started(self, component_id):
        '''
        Update ftrack when upload has started.
        '''

        data_string = json.dumps(
            {'type': 'uploadStarted', 'attachment': component_id}
        )

        self._update_ftrack(data_string)

    def on_upload_complete(self, component_id):
        '''
        Update ftrack when upload has completed.
        '''

        data_string = json.dumps({'type': 'uploadEnded', 'id': component_id})

        self._update_ftrack(data_string)

    def _update_ftrack(self, data_string):
        '''
        Update ftrack with json-formatedd *data_string*.
        '''
        logger.debug(f'_update_ftrack: {data_string}')

        data = data_string.encode('utf-8')
        data = base64.b64encode(data).decode('ascii')
        self._webActionWidget.page().runJavaScript(
            f'FT.updateFtrack("{data}")'
        )

    def ftrackExportAll(self, event):
        _token = event.contents()
        _name = event.name()
        logger.debug(f'ftrackExportAll: {_token} :: {_name}')

        # Add all the frames and export
        # Generate filenames that are unique
        # set name eg. Frame_159_1.jpg,Frame_159_2.jpg
        timestr = rvc.frame()
        # _filePath = fra._getFilePath('')
        _filePath = tempfile.gettempdir()
        tmpUpload = []
        _uuid = fra.ftrackUUID()

        # // Get all the annotated frames
        # // Function
        frames = []

        if event.name() == "ftrack-upload-frame":
            frames.push_back(rvc.frame())

        else:
            frames = rve.findAnnotatedFrames()

        self._annotatedFrames = frames
        logger.debug(f'frames : {frames})')

        for i in frames:
            tmpUpload.append(f"{_uuid}.jpg")

        session_name = os.path.join(_filePath, f'rvsession_{_uuid}.rv')

        self._doUpload = tmpUpload
        tmpSession = rvc.saveSession(session_name, True)
        logger.debug(f'tmpSession : {tmpSession}')

        args = [
            session_name,
            "-o",
            f"{_filePath}/{_uuid}.jpg",
            "-t",
            str(timestr),
            "-overlay",
            "frameburn",
            "0.8",
            "1.0",
            "30.0",
        ]

        logger.debug(f'rvsession args: {args}')

        self.uploadingCount(len(self._doUpload))
        if len(self._doUpload) > 0:
            self.rvio("Export Annotated Frames", args, self.uploadAll)

    def uploadAll(self):
        logger.debug(f'Uploading all annotated frames')
        logger.debug(f'self._doUpload {self._doUpload}')
        logger.debug(f'self._annotatedFrames {self._annotatedFrames}')
        for i, path in enumerate(self._doUpload):
            self.upload_annotation(path, i)

    def rvio(self, name, inargs, cleanup=None):
        rvioc = os.getenv('RV_APP_RVIO', 'rvio')
        cmd = [rvioc, '-v', '-err-to-out']
        license = os.getenv('RV_APP_USE_LICENSE_FILE')
        if license:
            cmd.append('-lic', license)

        cmd.extend(inargs)
        logger.debug(f'rvio cmd : {" ".join(cmd)}')
        proc = subprocess.Popen(cmd)
        proc.communicate()
        if cleanup:
            cleanup()


def createMode():
    return FtrackMode('webview')


def theMode():
    m = rvui.minorModeFromName('webview')
    return m
