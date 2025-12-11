# :coding: utf-8
# :copyright: Copyright (c) 2025 ftrack

import sys
import json
import re
import tempfile
import os
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
from rv import commands as rvc
from rv import extra_commands as rve
from rv import qtutils as rvq

import threading
import subprocess


class Runner(threading.Thread):
    """
    A thread class that runs a command and captures its output.

    This class extends threading.Thread to provide a way to execute shell commands
    in a separate thread, capturing both stdout and stderr output, and optionally
    cleaning up after execution.

    Attributes:
        cmd (list): The command to execute as a list of strings
        cleanup (callable, optional): A function to call after the command completes
        stdout (str): The captured stdout output from the command
        stderr (str): The captured stderr output from the command
    """

    def __init__(self, cmd, cleanup=None):
        """
        Initialize the Runner thread with a command and optional cleanup function.

        Args:
            cmd (list): The command to execute as a list of strings (shell=False)
            cleanup (callable, optional): A function to call after the command completes
        """
        self.stdout = None
        self.stderr = None
        self.cmd = cmd
        self.cleanup = cleanup
        threading.Thread.__init__(self)

    def run(self):
        """
        Execute the command in a subprocess and capture output.

        This method starts a subprocess with the provided command, captures both
        stdout and stderr, and calls the cleanup function if provided.

        Returns:
            None
        """
        p = subprocess.Popen(
            self.cmd,
            shell=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        self.stdout, self.stderr = p.communicate()
        if self.cleanup:
            self.cleanup()


class FtrackMode(rv.rvtypes.MinorMode):
    """
    A simple example that demonstrates how to create a minor mode for Ftrack integration.
    This mode handles shift-Z key binding to start/stop playback and provides functionality
    for connecting to Ftrack for asset and shot management.

    The mode initializes by setting up variables, checking environment settings,
    creating a session with Ftrack, and establishing keyboard bindings.
    """

    def __init__(self, name):
        """
        Initialize the FtrackMode instance.

        Args:
            name (str): The name of the minor mode instance
        """
        logger.debug('init')
        rv.rvtypes.MinorMode.__init__(self)

        self._name = name

        self.setup_variables()
        self.check_envs()
        self.create_session()
        self.create_bindings()

    @property
    def name(self):
        """Return the name of the plugin."""
        return self._name

    @property
    def session(self):
        """Return the session object for ftrack integration."""
        return self._session

    def create_session(self):
        """
        Creates and configures the ftrack API session with necessary locations.

        This method initializes the ftrack API session with auto-connect event hub disabled,
        then retrieves two important location objects: the origin location and the server location.
        These locations are stored as instance attributes for later use in the plugin.

        The origin location represents the source of the data, while the server location
        represents the server where the ftrack system is running. These locations are essential
        for proper session configuration and data handling within the plugin.
        """
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
        """
        Checks and sets up the required environment variables for Ftrack integration.

        This method first checks if a command-line URL is provided. If not, it verifies
        that the required environment variables (FTRACK_SERVER and FTRACK_API_KEY) are
        present. If a command-line URL is provided, it sets the FTRACK_SERVER environment
        variable to that URL. Additionally, it sets the REQUESTS_CA_BUNDLE environment
        variable to point to the cacert.pem file located in the plugin directory.

        Logs debug and info messages about the environment variables being checked and
        set.
        """
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
        """
        Creates a dock widget with a web action widget that loads a URL for review actions.

        This method sets up a dock widget containing a web view that displays review action
        interface. It initializes the necessary components including the base action widget,
        web navigation widget, and loads the review action URL. The method also sets up
        JavaScript export functionality for interaction with the web content.

        Args:
            data: Data passed to the action creation (not currently used in this implementation)

        Returns:
            None

        Raises:
            None (method does not explicitly raise exceptions)

        Note:
            - The method returns early if a dock action widget already exists
            - The URL is generated using the command line parameters
            - JavaScript export is enabled for the web page
        """
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
        """
        Creates and returns a QWidget containing a QWebEngineView widget for displaying content.

        This method sets up a widget with a vertical layout that contains a web view component.
        The web view is configured with appropriate spacing and margins, and is assigned a name
        for identification purposes.

        Returns:
            QtWidgets.QWidget: A widget containing the QWebEngineView for displaying web content
        """
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
        """
        Toggles the floating state of a dock widget based on the event content.

        This method is called when a floating state toggle event occurs in Ftrack.
        It takes an event containing an index value and creates a new dock widget
        with a title widget to display the floating dock.

        Args:
            event: The event object containing the index value that indicates
                which dock widget to toggle.

        Returns:
            None

        Example:
            When called with event.contents() = "1", this method will create
            a floating dock widget for the first dock widget in the application.
        """
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
        """
        Called when the mode is being shut down.

        This method handles cleanup operations when the Ftrack mode is being terminated.
        It rejects the event to prevent further processing and clears any loaded web content.

        Args:
            event: The event object that triggered the shutdown process
        """
        logger.debug('shutdown')
        event.reject()

        if self._webNavigationWidget:
            self._webNavigationWidget.page().setHtml("", QtCore.QUrl())

        if self._webActionWidget:
            self._webActionWidget.page().setHtml("", QtCore.QUrl())

    def ftrackEvent(self, event):
        """
        Handles a FTrack event by decoding its contents and updating the FTrack interface.

        This method receives a FTrack event, decodes its base64-encoded content, and creates
        a JavaScript string to update the FTrack interface with the event data.

        Args:
            event: The FTrack event object containing the event data

        Returns:
            None

        Raises:
            ValueError: If the event contents cannot be decoded from base64
            Exception: If there's an issue with creating the JavaScript content
        """
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
        """
        Toggles the title bar widget of a dock widget between a standard widget and the original title widget.

        This method changes the title bar widget of the given dock widget based on whether it's floating or not.
        If the dock widget is not floating, it replaces the title bar with a standard QWidget.
        If the dock widget is floating, it restores the original title widget as the title bar.

        Args:
            dockWidget: The dock widget whose title bar is to be toggled
            titleWidget: The original title widget that was used before floating
            ok: A boolean value that may be used to determine the toggle state (though not used in current implementation)

        Returns:
            None
        """
        logger.debug('toggleTitleBar')

        if not dockWidget.isFloating():
            dockWidget.setTitleBarWidget(QtWidgets.QWidget(self.mainWindow))

        else:
            dockWidget.setTitleBarWidget(QtWidgets.QWidget(titleWidget))

    def viewLoaded(self, view):
        """
        Called when a view is loaded in the application interface.

        This method is invoked when a view is loaded, allowing the plugin to
        customize the view's dimensions and behavior. It sets the view's width
        and height constraints to allow flexible sizing.

        Args:
            view: The view object that is being loaded. This is typically a
                Qt widget or similar interface element.

        Returns:
            None
        """
        logger.debug('viewLoaded')

        view.setMaximumWidth(16777215)
        view.setMinimumWidth(0)
        view.setMaximumHeight(16777215)
        view.setMinimumHeight(250)

    def initUi(self):
        """
        Initialize the user interface for the plugin's navigation widget.

        This method sets up the dock widget with navigation functionality by:
        1. Checking if this is the first render to avoid redundant initialization
        2. Checking a URL for navigation based on command line parameters
        3. Creating a dock widget with the navigation content
        4. Configuring the web view to load the navigation URL
        5. Setting up event handlers for view loading and dock widget changes
        6. Adding the dock widget to the main window and making it visible

        If no server is available (no URL can be generated), it falls back to a local HTML file.

        Returns:
            None
        """
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
        """
        Called when the current frame changes in the timeline.

        This method extracts the source index from the current frame's source name,
        compares it with the previously tracked source, and if it has changed,
        sends a message to update the Ftrack UI with the new source index.

        Args:
            event: The event object containing frame change information

        Returns:
            None

        """
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
        """
        Handles changes to the navigation group in the interface.

        Args:
            event: A dictionary containing information about the navigation group change event.
                Specifically, it contains the 'contents' key which holds the group name.

        Example:
            If the event contains 'contents' with value "group1", this method will set
            the view node to "sourceGroup00000group1".

        """
        logger.debug(f'navGroupChanged {event}')
        self.setViewNode("sourceGroup00000" + event.contents())

    def ftrackToggle(self, event):
        """
        Toggles the visibility of the FTrack panels.

        This method checks if the panels are currently hidden. If they are hidden,
        it shows the panels, resets the hidden state, and initializes the UI.
        If the panels are already visible, it hides them and sets the hidden state to True.

        Args:
            event: The event object that triggered this method (typically from a UI event)

        Returns:
            None
        """
        logger.debug(f'ftrackToggle {event}')

        if self._isHidden:
            self._isHidden = False
            self.showPanels()
            self.initUi()
        else:
            self._isHidden = True
            self.hidePanels()

    def hidePanels(self):
        """
        Hides all navigation and action panels in the interface.

        This method hides the base and dock versions of both navigation and action widgets,
        which are typically used for UI navigation and tool access in the application.

        The method is called when the user wants to hide panels, possibly during:
        - Interface customization
        - Minimizing the interface footprint
        - When transitioning between different views

        Note: This method only hides the panels - it does not remove them from the UI.
        """
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
        """
        Display all navigation and action panels in the interface.

        This method shows the base and dock versions of both navigation and action widgets.
        It is typically called when the user wants to restore visibility of panels that may
        have been hidden or minimized.

        The method performs the following actions:
        - Shows the base navigation widget if it exists
        - Shows the dock navigation widget if it exists
        - Shows the base action widget if it exists
        - Shows the dock action widget if it exists

        This method is useful for restoring the user interface to a full-featured state
        after panels have been hidden or minimized.
        """
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
        """
        Toggles whether Ftrack panels should be shown on startup.

        This method checks the current state of the showPanelsOnStartup setting and
        updates it accordingly. When toggled on, it saves the setting to enable panels
        to appear on startup. When toggled off, it saves the setting to disable panels
        from appearing on startup.

        Args:
            event: The event object passed by Ftrack when the toggle is triggered

        Returns:
            None
        """
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
        """Return the menu state based on whether the panel is hidden."""
        logger.debug("panelState: %s" % self._isHidden)
        return (
            rvc.CheckedMenuState if self._isHidden else rvc.UncheckedMenuState
        )

    def showPanelsOnStartupState(self):
        """
        Determines the menu state for panels based on whether they should be shown on startup.

        Returns:
            rvc.CheckedMenuState or rvc.UncheckedMenuState:
                - rvc.CheckedMenuState if panels should be shown on startup
                - rvc.UncheckedMenuState if panels should not be shown on startup
        """
        logger.debug("show on startup: %s" % self._showPanelsOnStartup)
        return (
            rvc.CheckedMenuState
            if self._showPanelsOnStartup
            else rvc.UncheckedMenuState
        )

    def create_bindings(self):
        """
        Sets up event bindings and UI initialization for the FTrack plugin.

        This method configures various event listeners that respond to FTrack-related
        actions and user interactions. It initializes the plugin's UI state and
        creates menu items for user access to FTrack functionality.

        The bindings include:
        - ftrack-event: General FTrack event handling
        - ftrack-timeline-loaded: Creates action window when user logs in
        - ftrack-toggle-floating: Toggles visibility of floating panels
        - frame-changed: Handles frame changes in the timeline
        - ftrack-changed-group: Handles group selection changes
        - ftrack-upload-frame: Uploads current frame to FTrack
        - ftrack-upload-frames: Uploads all annotated frames to FTrack

        Also sets up a context menu with options to toggle panels and access
        preferences, including a setting to show panels on startup.
        """
        logger.debug('create_bindings')

        self._showPanelsOnStartup = rvc.readSettings(
            "ftrackMode", "showPanelsOnStartUp", True
        )

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
                        lambda: rvc.NeutralMenuState,
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

        if self._showPanelsOnStartup:
            self._isHidden = False
            self.initUi()

        else:
            self._isHidden = True

    def setup_variables(self):
        """
        Initialize and set up various variables and references for the plugin.

        This method is called during plugin initialization to:
        - Create a reference to the main RVQ session window
        - Set up internal state variables for tracking component paths and session state
        - Initialize reference to source nodes (sequence, stack, layout)
        - Prepare binding systems for event handling
        - Set up flags for panel visibility and debugging

        The method establishes the foundation for the plugin's functionality by:
        - Caching filesystem paths for components to ensure consistency during the session
        - Setting up event bindings for UI interactions
        - Initializing state variables that control plugin behavior

        Note: This method is called once during plugin initialization and sets up the
        initial state that will be used throughout the session.
        """
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

    def uploadAll(self):
        """
        Upload all annotated frames to the ftrack system.

        This method iterates through the list of frames that need to be uploaded
        and calls the upload_annotation method for each frame. It processes each
        frame in the order defined by the _doUpload list, which contains the
        frame data and the corresponding annotated frames.

        The method logs a debug message to indicate that it's uploading all frames,
        and then processes each frame in the _doUpload list with its associated
        annotated frames.

        Note:
            - The method assumes that self._doUpload and self._annotatedFrames
            are properly initialized with the frame data and annotations.
            - Each call to upload_annotation will upload the specified frame
            with its associated annotations to the ftrack system.

        """
        logger.debug('Upload all frames')
        for i in self._doUpload:
            self.upload_annotation(self._doUpload[i], self._annotatedFrames[i])

    def uploadingCount(self, count):
        """
        Updates the Ftrack UI with the current upload count.

        This method encodes a JSON payload containing the upload count and sends it
        to the Ftrack web interface using JavaScript. The payload includes a 'type'
        field set to 'uploadCount' and the provided count value.

        Args:
            count (int): The current upload count to display in the Ftrack UI

        """
        logger.debug(f'uploadingCount: {count}')

        data = base64.b64encode(
            json.dumps({'type': 'uploadCount', 'count': count}).encode("utf-8")
        ).decode('ascii')

        self._webActionWidget.page().runJavaScript(
            f'FT.updateFtrack("{data}")'
        )

    def upload_annotation(self, filename, frame):
        """
        Upload a single annotation saved as *filename*.

        This method creates a component from the given file and frame information,
        adds it to the note form, and uploads it to the ftrack server.

        The process involves:
        1. Creating a component with the specified file and frame data
        2. Adding the component to the note form interface
        3. Uploading the component to the ftrack server location

        Parameters:
        -----------
        filename : str
            The path to the annotation file to be uploaded
        frame : int
            The frame number associated with the annotation

        Returns:
        --------
        None

        Events:
        -------
        on_upload_started(component_id) : Called when component creation begins
            - component_id : str, the unique identifier of the created component
        on_upload_complete(component_id) : Called when upload is successfully completed
            - component_id : str, the unique identifier of the uploaded component

        Notes:
        ------
        - The method uses JSON encoding to pass the file name and frame information
        - The component creation and upload process is asynchronous
        - Error handling is assumed to be managed by the parent class or framework
        - The component ID is used for tracking and reference throughout the upload process
        """
        logger.debug(f'uploading file : {filename}')

        encoded_args = json.dumps({'file_name': filename, 'frame': frame})

        component_id = fra.create_component(encoded_args)
        logger.debug(f'created component : {component_id}')
        self.on_upload_started(component_id)

        fra.upload_component(component_id)
        logger.debug(f'Upload completed')
        self.on_upload_complete(component_id)

    def on_upload_started(self, component_id):
        """
        Update Ftrack when an upload has started.

        This method is triggered when an upload process begins in the application.
        It sends a notification to Ftrack with the type 'uploadStarted' and the
        component ID of the file being uploaded.

        The notification allows Ftrack to track upload activities, monitor progress,
        and provide status updates to users or other systems.

        Args:
            component_id (str): The unique identifier of the component being uploaded.
                            This is typically a file or asset identifier within the
                            application's system.

        Returns:
            None

        Raises:
            ValueError: If component_id is None or empty.
            json.JSONEncodeError: If the data string cannot be serialized to JSON.

        """
        data_string = json.dumps(
            {'type': 'uploadStarted', 'attachment': component_id}
        )

        self._update_ftrack(data_string)

    def on_upload_complete(self, component_id):
        """
        Update ftrack when upload has completed.

        This method is called after a file upload operation has successfully
        completed. It sends a notification to the Ftrack server indicating
        that the upload has ended, allowing Ftrack to update its internal
        state accordingly.

        Args:
            component_id (str): The unique identifier of the component that
                               was uploaded. This ID is used to correlate the
                               upload event with the specific asset or item
                               in Ftrack.

        Returns:
            None

        Note:
            - The method serializes the event data using JSON
            - The event type is set to 'uploadEnded'
            - This method should only be called after a successful upload
              operation to ensure data consistency
        """
        data_string = json.dumps({'type': 'uploadEnded', 'id': component_id})

        self._update_ftrack(data_string)

    def _update_ftrack(self, data_string):
        """
        Update Ftrack with JSON-formatted data string.

        This method encodes the provided data_string to base64 and sends it to the Ftrack
        integration through JavaScript. The data is first encoded as UTF-8 bytes, then
        base64-encoded to ASCII, and passed to the FT.updateFtrack() JavaScript function.

        Args:
            data_string (str): A JSON-formatted string containing the data to be updated in Ftrack.

        Returns:
            None

        Notes:
            - The method uses base64 encoding to safely transmit the data string.
            - The encoded data is passed to the Ftrack integration via JavaScript.
            - This method logs the data string for debugging purposes.
        """
        logger.debug(f'_update_ftrack: {data_string}')

        data = data_string.encode('utf-8')
        data = base64.b64encode(data).decode('ascii')
        self._webActionWidget.page().runJavaScript(
            f'FT.updateFtrack("{data}")'
        )

    def ftrackExportAll(self, event):
        """
        Handles the export of annotated frames to Ftrack by:
        1. Retrieving the event data (token and name)
        2. Identifying annotated frames
        3. Generating unique filenames with frame numbers
        4. Creating a temporary RV session with the frames
        5. Exporting the frames with frame burn overlay

        Parameters:
            event (Event): The Ftrack event containing metadata about the operation

        Returns:
            None

        Side Effects:
            - Creates temporary session files in system temp directory
            - Generates and stores frame export filenames
            - Triggers RV export process with frame burn overlay
            - Updates upload progress count

        Note:
            This method handles both "ftrack-upload-frame" events (single frame)
            and general annotated frame exports. It generates unique filenames
            using a UUID and frame number format: <uuid>_<frame_number>.jpg
            The export uses RV's frame burn overlay with 80% opacity, 100% brightness,
            and 30ms duration.

        """
        _token = event.contents()
        _name = event.name()
        logger.debug(f'ftrackExportAll: {_token} :: {_name}')

        # Add all the frames and export
        # Generate filenames that are unique
        # set name eg. Frame_159_1.jpg,Frame_159_2.jpg
        # _filePath = fra._getFilePath('')
        _filePath = tempfile.gettempdir()
        tmpUpload = []
        _uuid = fra.ftrackUUID()

        # // Get all the annotated frames
        # // Function
        frames = []

        if event.name() == "ftrack-upload-frame":
            frames.append(rvc.frame())

        else:
            frames = rve.findAnnotatedFrames()

        self._annotatedFrames = frames
        logger.debug(f'frames : {frames})')

        for i in frames:
            fpadd = "%04d" % i
            tmpUpload.append(f"{_uuid}_{fpadd}.jpg")

        session_name = os.path.join(_filePath, f'rvsession_{_uuid}.rv')

        self._doUpload = tmpUpload
        tmpSession = rvc.saveSession(session_name, True)
        logger.debug(f'tmpSession : {tmpSession}')

        args = [
            session_name,
            "-o",
            f"{_filePath}/{_uuid}_#.jpg",
            "-t",
            ','.join([str(f) for f in frames]),
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
        """
        Uploads all annotated frames to the Ftrack server.

        This method iterates through the list of frames that need to be uploaded
        (stored in self._doUpload) and calls the upload_annotation method for each
        frame. The upload process is logged with debug messages to track progress.

        The method performs the following steps:
        1. Logs debug information about the upload process
        2. Iterates through each frame path in self._doUpload
        3. Calls upload_annotation for each frame with its index

        Note: This method assumes that self._doUpload contains paths to annotated frames
        that need to be uploaded to Ftrack. The upload_annotation method handles the
        actual upload logic.

        Returns:
            None
        """
        logger.debug(f'Uploading all annotated frames')
        logger.debug(f'self._doUpload {self._doUpload}')
        logger.debug(f'self._annotatedFrames {self._annotatedFrames}')
        for i, path in enumerate(self._doUpload):
            self.upload_annotation(path, i)

    def rvio(self, name, inargs, cleanup=None):
        """
        Launches the RVIO application with specified arguments.

        This method constructs and executes a command to run the RV IO (rvio) application
        with the provided input arguments. It handles environment variables for license
        management and error output redirection.

        Args:
            name (str): The name of the operation or resource being processed
            inargs (list): List of command-line arguments to pass to rvio
            cleanup (callable, optional): Function to call when the process completes or fails

        Returns:
            subprocess.Popen: The started process object

        Raises:
            RuntimeError: If the rvio command cannot be executed or starts unsuccessfully

        Environment variables used:
            RV_APP_RVIO: Path to the rvio executable (default: 'rvio')
            RV_APP_USE_LICENSE_FILE: Path to license file (if provided)

        Note:
            The command includes -v for verbose output and -err-to-out to redirect error
            messages to standard output. The method logs the full command for debugging.
        """
        rvioc = os.getenv('RV_APP_RVIO', 'rvio')
        cmd = [rvioc, '-v', '-err-to-out']
        license = os.getenv('RV_APP_USE_LICENSE_FILE')
        if license:
            cmd.append('-lic', license)

        cmd.extend(inargs)
        logger.debug(f'rvio cmd : {" ".join(cmd)}')
        proc = Runner(cmd, cleanup)
        proc.start()


def createMode():
    """
    Create and return a FtrackMode instance.

    Returns:
        FtrackMode: An instance of the FtrackMode class
    """
    return FtrackMode('webview')


def theMode():
    """
    Retrieve the FtrackMode instance by name.

    Returns:
        FtrackMode: The FtrackMode instance if found, otherwise None
    """
    m = rv.minorModeFromName('webview')
    return m
