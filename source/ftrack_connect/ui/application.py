# :coding: utf-8
# :copyright: Copyright (c) 2014 ftrack

import os
import getpass

from PySide import QtGui
from PySide import QtCore

import ftrack_connect.event_hub_thread
import ftrack_connect.error
import ftrack_connect.ui.theme
from ftrack_connect.ui.widget import uncaught_error as _uncaught_error
from ftrack_connect.ui.widget import tab_widget as _tab_widget
from ftrack_connect.ui.widget import login as _login
from ftrack_connect.error import NotUniqueError as _NotUniqueError


class ApplicationPlugin(QtGui.QWidget):
    '''Base widget for ftrack connect application plugin.'''

    #: Signal to emit to request focus of this plugin in application.
    requestApplicationFocus = QtCore.Signal(object)

    #: Signal to emit to request closing application.
    requestApplicationClose = QtCore.Signal(object)

    def getName(self):
        '''Return name of widget.'''
        return self.__class__.__name__

    def getIdentifier(self):
        '''Return identifier for widget.'''
        return self.getName().lower().replace(' ', '.')


class Application(QtGui.QMainWindow):
    '''Main application window for ftrack connect.'''

    #: Signal when login fails.
    loginError = QtCore.Signal(object)

    #: Signal when event received via ftrack's event hub.
    eventHubSignal = QtCore.Signal(object)

    def __init__(self, *args, **kwargs):
        '''Initialise the main application window.'''
        theme = kwargs.pop('theme', 'light')
        super(Application, self).__init__(*args, **kwargs)

        # Register widget for error handling.
        self.uncaughtError = _uncaught_error.UncaughtError(
            parent=self
        )

        if not QtGui.QSystemTrayIcon.isSystemTrayAvailable():
            raise ftrack_connect.error.ConnectError(
                'No system tray located.'
            )

        self.logoIcon = QtGui.QIcon(
            QtGui.QPixmap(':/ftrack/image/default/ftrackLogoColor')
        )

        self._theme = None
        self.setTheme(theme)

        self.plugins = {}

        self._initialiseTray()

        self.setObjectName('ftrack-connect-window')
        self.setWindowTitle('ftrack connect')
        self.resize(450, 700)
        self.move(50, 50)

        self.setWindowIcon(self.logoIcon)

        self.loginWidget = None
        self.login()

    def theme(self):
        '''Return current theme.'''
        return self._theme

    def setTheme(self, theme):
        '''Set *theme*.'''
        self._theme = theme
        ftrack_connect.ui.theme.applyTheme(self, self._theme)

    def toggleTheme(self):
        '''Toggle active application theme.'''
        if self.theme() == 'dark':
            self.setTheme('light')
        else:
            self.setTheme('dark')

    def _onConnectTopicEvent(self, event):
        '''Generic callback for all ftrack.connect events.

        .. note::
            Events not triggered by the current logged in user will be dropped.

        '''
        if event['topic'] != 'ftrack.connect':
            return

        self._routeEvent(event)

    def logout(self):
        '''Clear stored credentials and quit Connect.'''
        settings = QtCore.QSettings()
        settings.remove('login')

        QtGui.qApp.quit()

    def login(self):
        '''Login using stored credentials or ask user for them.'''

        # Get settings from store.
        settings = QtCore.QSettings()
        server = settings.value('login/server', None)
        username = settings.value('login/username', None)
        apiKey = settings.value('login/apikey', None)

        # If missing any of the settings bring up login dialog.
        if None in (server, username, apiKey):
            self.showLoginWidget()
        else:
            # Show login screen on login error.
            self.loginError.connect(self.showLoginWidget)

            # Try to login.
            self.loginWithCredentials(server, username, apiKey)

    def showLoginWidget(self):
        '''Show the login widget.'''
        if self.loginWidget is None:
            self.loginWidget = _login.Login()
            self.setCentralWidget(self.loginWidget)
            self.loginWidget.login.connect(self.loginWithCredentials)
            self.loginError.connect(self.loginWidget.loginError.emit)
            self.focus()

            # Set focus on the login widget to remove any focus from its child
            # widgets.
            self.loginWidget.setFocus()

    def loginWithCredentials(self, url, username, apiKey):
        '''Connect to *url* with *username* and *apiKey*.

        loginError will be emitted if this fails.

        '''
        os.environ['FTRACK_SERVER'] = url
        os.environ['LOGNAME'] = username
        os.environ['FTRACK_APIKEY'] = apiKey

        # Import ftrack module and catch any errors.
        try:
            import ftrack

            # Force update the url of the server in case it was already set.
            ftrack.xmlServer.__init__('{url}/client/'.format(url=url), False)

            # Force update event hub since it will set the url on initialise.
            ftrack.EVENT_HUB.__init__()

        except Exception as error:

            # Catch connection error since ftrack module will connect on load.
            if str(error).find('Unable to connect on') >= 0:
                self.loginError.emit(str(error))

            # Reraise the error.
            raise

        # Access ftrack to validate login details.
        try:
            ftrack.getUUID()
        except ftrack.FTrackError as error:
            self.loginError.emit(str(error))
        else:
            # Store login details in settings.
            settings = QtCore.QSettings()
            settings.setValue('login/server', url)
            settings.setValue('login/username', username)
            settings.setValue('login/apikey', apiKey)

            self.configureConnectAndDiscoverPlugins()

    def configureConnectAndDiscoverPlugins(self):
        '''Configure connect and load plugins.'''

        # Local import to avoid connection errors.
        import ftrack
        ftrack.setup()
        self.tabPanel = _tab_widget.TabWidget()
        self.tabPanel.tabBar().setObjectName('application-tab-bar')
        self.setCentralWidget(self.tabPanel)

        self._discoverPlugins()

        ftrack.EVENT_HUB.subscribe(
            'topic=ftrack.connect and source.user.username={0}'.format(
                getpass.getuser()
            ),
            self._relayEventHubEvent
        )
        self.eventHubSignal.connect(self._onConnectTopicEvent)

        import ftrack_connect.event_hub_thread
        self.eventHubThread = ftrack_connect.event_hub_thread.EventHubThread()
        self.eventHubThread.start()

        self.focus()

    def _relayEventHubEvent(self, event):
        '''Relay all ftrack.connect events.'''
        self.eventHubSignal.emit(event)

    def _initialiseTray(self):
        '''Initialise and add application icon to system tray.'''
        self.trayMenu = self._createTrayMenu()

        self.tray = QtGui.QSystemTrayIcon(self)

        self.tray.setContextMenu(
            self.trayMenu
        )

        self.tray.setIcon(self.logoIcon)
        self.tray.show()

    def _createTrayMenu(self):
        '''Return a menu for system tray.'''
        menu = QtGui.QMenu(self)

        logoutAction = QtGui.QAction(
            'Log Out && Quit', self,
            triggered=self.logout
        )

        quitAction = QtGui.QAction(
            'Quit', self,
            triggered=QtGui.qApp.quit
        )

        focusAction = QtGui.QAction(
            'Open', self,
            triggered=self.focus
        )

        styleAction = QtGui.QAction(
            'Change Theme', self,
            triggered=self.toggleTheme
        )
        menu.addAction(focusAction)
        menu.addSeparator()
        menu.addAction(styleAction)
        menu.addSeparator()
        menu.addAction(logoutAction)
        menu.addSeparator()
        menu.addAction(quitAction)

        return menu

    def _discoverPlugins(self):
        '''Find and load tab plugins in search paths.'''
        #: TODO: Add discover functionality and search paths.

        # Add publisher as a plugin.
        from .publisher import register
        register(self)

    def _routeEvent(self, event):
        '''Route websocket *event* to publisher plugin.

        Expect event['data'] to contain:

            * plugin - The name of the plugin to route to.
            * action - The action to execute on the plugin.

        Raise `ConnectError` if no plugin is found or if action is missing on
        plugin.

        '''
        plugin = event['data']['plugin']
        action = event['data']['action']

        try:
            pluginInstance = self.plugins[plugin]
        except KeyError:
            raise ftrack_connect.error.ConnectError(
                'Plugin "{0}" not found.'.format(
                    plugin
                )
            )

        try:
            method = getattr(pluginInstance, action)
        except AttributeError:
            raise ftrack_connect.error.ConnectError(
                'Method "{0}" not found on "{1}" plugin({2}).'.format(
                    action, plugin, pluginInstance
                )
            )

        method(event)

    def _onWidgetRequestApplicationFocus(self, widget):
        '''Switch tab to *widget* and bring application to front.'''
        self.tabPanel.setCurrentWidget(widget)
        self.focus()

    def _onWidgetRequestApplicationClose(self, widget):
        '''Hide application upon *widget* request.'''
        self.hide()

    def addPlugin(self, plugin, name=None, identifier=None):
        '''Add *plugin* in new tab with *name* and *identifier*.

        *plugin* should be an instance of :py:class:`ApplicationPlugin`.

        *name* will be used as the label for the tab. If *name* is None then
        plugin.getName() will be used.

        *identifier* will be used for routing events to plugins. If
        *identifier* is None then plugin.getIdentifier() will be used.

        '''
        if name is None:
            name = plugin.getName()

        if identifier is None:
            identifier = plugin.getIdentifier()

        if identifier in self.plugins:
            raise _NotUniqueError(
                'Cannot add plugin. An existing plugin has already been '
                'registered with identifier {0}.'.format(identifier)
            )

        self.plugins[identifier] = plugin
        self.tabPanel.addTab(plugin, name)

        # Connect standard plugin events.
        plugin.requestApplicationFocus.connect(
            self._onWidgetRequestApplicationFocus
        )
        plugin.requestApplicationClose.connect(
            self._onWidgetRequestApplicationClose
        )

    def removePlugin(self, identifier):
        '''Remove plugin registered with *identifier*.

        Raise :py:exc:`KeyError` if no plugin with *identifier* has been added.

        '''
        plugin = self.plugins.get(identifier)
        if plugin is None:
            raise KeyError(
                'No plugin registered with identifier "{0}".'.format(identifier)
            )

        index = self.tabPanel.indexOf(plugin)
        self.tabPanel.removeTab(index)

        plugin.deleteLater()
        del self.plugins[identifier]

    def focus(self):
        '''Focus and bring the window to top.'''
        self.activateWindow()
        self.show()
        self.raise_()
