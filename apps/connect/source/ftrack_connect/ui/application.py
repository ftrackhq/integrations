# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import copy
import os
import platform
import sys
import requests
import requests.exceptions
import uuid
import logging
import weakref
from operator import itemgetter
import time
import qtawesome as qta

import ftrack_api
import ftrack_api._centralized_storage_scenario
import ftrack_api.event.base

from ftrack_utils.usage import (
    set_usage_tracker,
    get_usage_tracker,
    UsageTracker,
)

try:
    from PySide6 import QtWidgets, QtCore, QtGui
    from PySide6.QtGui import QAction
except ImportError:
    from PySide2 import QtWidgets, QtCore, QtGui
    from PySide2.QtWidgets import QAction

from ftrack_connect import load_fonts_resource
import ftrack_connect
import ftrack_connect.event_hub_thread as _event_hub_thread
import ftrack_connect.error
from ftrack_connect.utils.plugin import (
    get_default_plugin_directory,
    get_plugins_from_path,
    get_plugin_data,
    PLUGIN_DIRECTORIES,
)
from ftrack_connect.utils.credentials import (
    load_credentials,
    store_credentials,
)
from ftrack_connect.utils.directory import open_directory
import ftrack_connect.ui.theme
import ftrack_connect.ui.widget.overlay
from ftrack_connect.ui.widget import uncaught_error as _uncaught_error
from ftrack_connect.ui.widget import tab_widget as _tab_widget
from ftrack_connect.ui.widget import login as _login
from ftrack_connect.ui.widget import about as _about
from ftrack_connect.ui import login_tools as _login_tools
from ftrack_connect.ui.widget import configure_scenario as _scenario_widget
import ftrack_connect.utils.log
from ftrack_connect.application_launcher.discover_applications import (
    DiscoverApplications,
)

from ftrack_connect.utils.plugin import create_target_plugin_directory


class ConnectWidgetPlugin(object):
    topic = 'ftrack.connect.plugin.connect-widget'

    def __init__(self, connect_widget):
        '''Initialise class with non initialised connect_widget.'''
        if not isinstance(connect_widget, type):
            raise Exception(
                'Widget class {} should be non initialised'.format(
                    connect_widget
                )
            )

        self._connect_widget = connect_widget

    def _return_widget(self, event):
        '''Return stored widget class.'''
        return self._connect_widget

    def register(self, session, priority):
        '''register a new connect widget with given **priority**.'''
        session.event_hub.subscribe(
            'topic={0} '
            'and source.user.username={1}'.format(
                self.topic, session.api_user
            ),
            self._return_widget,
            priority=priority,
        )


class ConnectWidget(QtWidgets.QWidget):
    '''Base widget for ftrack connect application plugin.'''

    icon = None
    name = None

    #: Signal to emit to request focus of this plugin in application.
    requestApplicationFocus = QtCore.Signal(object)

    #: Signal to emit to request closing application.
    requestApplicationClose = QtCore.Signal(object)

    #: Signal to emit to request connect to restart.
    requestConnectRestart = QtCore.Signal()

    #: Signal to fetch discovered plugins
    fetchPlugins = QtCore.Signal(object)

    @property
    def session(self):
        '''Return current session.'''
        return self._session

    def __init__(self, session, parent=None):
        '''Initialise class with ftrack *session* and *parent* widget.'''
        super(ConnectWidget, self).__init__(parent=parent)
        self._session = session

    def getName(self):
        '''Return name of widget.'''
        return self.name or self.__class__.__name__

    def getIdentifier(self):
        '''Return identifier for widget.'''
        return self.getName().lower().replace(' ', '.')

    def refresh(self):
        '''Refresh/rebuild widget, called when widget has been fully set up. Should be overridden'''
        pass

    def get_debug_information(self):
        '''Return debug information for about dialog, should be overriden.'''
        return {
            'name': self.getName(),
            'identifier': self.getIdentifier(),
        }


class Application(QtWidgets.QMainWindow):
    '''Main application window for ftrack connect.'''

    #: Signal when login fails.
    loginError = QtCore.Signal(object)

    #: Signal when event received via ftrack's event hub.
    eventHubSignal = QtCore.Signal(object)

    # Login signal.
    loginSignal = QtCore.Signal(object, object, object)
    loginSuccessSignal = QtCore.Signal()

    _builtin_widget_plugins = []
    _widget_plugin_instances = {}

    @property
    def session(self):
        '''Return current session.'''
        return self._session

    @property
    def plugins(self):
        return self._plugins

    def __init__(self, theme='system', instance=None, log_level=None):
        '''Initialise the main application window with *theme*, singleton
        *instance* and custom *log_level*.'''
        super(Application, self).__init__()
        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )
        self._instance = instance
        self._session = None
        self.__connect_start_time = time.time()
        self._log_level = log_level

        self._discovered_plugins = (
            self._discover_plugin_data_from_plugin_directories()
        )
        self._plugins = self._available_plugin_data_from_plugin_directories()

        # Register widget for error handling.
        self.uncaughtError = _uncaught_error.UncaughtError(
            parent=self.centralWidget()
        )

        self._login_server_thread = None
        self.tray = None
        if not QtWidgets.QSystemTrayIcon.isSystemTrayAvailable():
            QtWidgets.QMessageBox.warning(
                self,
                'Connect',
                'No system tray located.\n\nHint: On '
                'Linux CentOS consider installing '
                'gnome-shell-extension-top-icons',
            )
        else:
            self._initialise_tray()
        self._initialise_menu_bar()

        self._set_theme(theme)

        self._application_launcher = None

        self.setObjectName('ftrack-connect-window')
        self.setWindowTitle('ftrack Connect')
        self.resize(450, 700)
        self.move(50, 50)

        self._login_overlay = None
        self._login_widget = _login.Login(theme=self.theme())
        self.loginSignal.connect(self.loginWithCredentials)
        self.loginSuccessSignal.connect(self._post_login_settings)
        self.login()

    def restart(self):
        '''restart connect application'''
        self.logger.info('Connect restarting....')
        QtWidgets.QApplication.quit()
        self._instance.__del__()

        # Give enough time to ensure the lockfile has been removed
        while os.path.exists(self._instance.lockfile):
            time.sleep(0.1)
        process = QtCore.QProcess()

        path = QtCore.QCoreApplication.applicationFilePath()
        args = QtCore.QCoreApplication.arguments()

        # Check if Connect is frozen (cx_freeze) and act accordingly.
        if not hasattr(sys, 'frozen'):
            path = sys.executable
        else:
            args.pop(0)

        status = -1

        self.logger.debug(
            f'Connect restarting with :: path: {path} argv: {args}'
        )
        try:
            status = process.startDetached(path, args)
        except Exception as error:
            self.logger.exception(str(error))

        self.logger.debug(f'Connect restarted with status {status}')

        return status

    def ftrack_title_icon(self, theme=None):
        logo_path = ':ftrack/titlebar/logo'
        return logo_path

    def ftrack_tray_icon(self, theme=None):
        logo_path = ':ftrack/logo/{}'

        theme = theme or self.system_theme()
        if platform.system() == 'Darwin':
            result_logo = logo_path.format('darwin/{}'.format(theme))
        else:
            result_logo = self.ftrack_title_icon(theme)

        return result_logo

    def system_theme(self, fallback='light'):
        # replicate content of https://github.com/albertosottile/darkdetect/blob/master/darkdetect/__init__.py
        # as does not work when frozen
        if sys.platform == "darwin":
            from darkdetect import _mac_detect as stylemodule

        elif (
            sys.platform == "win32"
            and platform.release().isdigit()  # Windows 8.1 would result in '8.1' str
            and int(platform.release()) >= 10
        ):
            from darkdetect import _windows_detect as stylemodule

        elif sys.platform == "linux":
            from darkdetect import _linux_detect as stylemodule

        else:
            from darkdetect import _dummy as stylemodule

        current_theme = stylemodule.theme()
        if not current_theme:
            self.logger.warning(
                'System theme could not be determined, using: light'
            )
            current_theme = fallback

        return current_theme.lower()

    def emitConnectUsage(self):
        '''Emit data to intercom to track Connect data usage'''
        connect_stopped_time = time.time()

        metadata = {
            'label': 'ftrack-connect',
            'version': ftrack_connect.__version__,
            'os': platform.platform(),
            'session-duration': connect_stopped_time
            - self.__connect_start_time,
        }

        usage_tracker = get_usage_tracker()
        if usage_tracker:
            usage_tracker.track('USED-CONNECT', metadata)

    def _post_login_settings(self):
        if self.tray:
            self.tray.show()

    def _assign_session_theme(self, theme):
        if self.session:
            self.session.connect_theme = theme

    def theme(self):
        '''Return current theme.'''
        return self._theme

    def _set_theme(self, theme='system'):
        '''Set *theme*.'''
        if theme not in ['light', 'dark']:
            theme = self.system_theme()

        self.logger.debug('Setting theme {}'.format(theme))
        self._theme = theme

        self.setWindowIcon(
            QtGui.QIcon(QtGui.QPixmap(self.ftrack_title_icon(theme)))
        )
        if self.tray:
            self.tray.setIcon(
                QtGui.QIcon(QtGui.QPixmap(self.ftrack_tray_icon(theme)))
            )

        qtawesome_style = getattr(qta, theme)
        qtawesome_style(QtWidgets.QApplication.instance())

        ftrack_connect.ui.theme.applyFont()
        ftrack_connect.ui.theme.applyTheme(self, self.theme(), 'cleanlooks')

    def _onConnectTopicEvent(self, event):
        '''Generic callback for all ftrack.connect events.

        .. note::
            Events not triggered by the current logged in user will be dropped.

        '''
        if event['topic'] != 'ftrack.connect':
            return

        self._route_event(event)

    def logout(self):
        '''Clear stored credentials and quit Connect.'''
        self._clear_qsettings()
        config = load_credentials()

        config['accounts'] = []
        store_credentials(config)

        QtWidgets.QApplication.quit()

    def _clear_qsettings(self):
        '''Remove credentials from QSettings.'''
        settings = QtCore.QSettings()
        settings.remove('login')

    def _get_credentials(self):
        '''Return a dict with API credentials from storage.'''
        credentials = None

        # Read from json config file.
        json_config = load_credentials()
        if json_config:
            try:
                data = json_config['accounts'][0]
                credentials = {
                    'server_url': data['server_url'],
                    'api_user': data['api_user'],
                    'api_key': data['api_key'],
                }
            except Exception:
                self.logger.debug(
                    u'No credentials were found in config: {0}.'.format(
                        json_config
                    )
                )

        # Fallback on old QSettings.
        if not json_config and not credentials:
            settings = QtCore.QSettings()
            server_url = settings.value('login/server', None)
            api_user = settings.value('login/username', None)
            api_key = settings.value('login/apikey', None)

            if not None in (server_url, api_user, api_key):
                credentials = {
                    'server_url': server_url,
                    'api_user': api_user,
                    'api_key': api_key,
                }

        return credentials

    def _save_credentials(self, server_url, api_user, api_key):
        '''Save API credentials to storage.'''
        # Clear QSettings since they should not be used any more.
        self._clear_qsettings()

        # Save the credentials.
        json_config = load_credentials()

        if not json_config:
            json_config = {}

        # Add a unique id to the config that can be used to identify this
        # machine.
        if not 'id' in json_config:
            json_config['id'] = str(uuid.uuid4())

        json_config['accounts'] = [
            {
                'server_url': server_url,
                'api_user': api_user,
                'api_key': api_key,
            }
        ]

        store_credentials(json_config)

    def login(self):
        '''Login using stored credentials or ask user for them.'''
        credentials = self._get_credentials()
        self._show_login_widget()

        if credentials:
            # Try to login.
            self.loginWithCredentials(
                credentials['server_url'],
                credentials['api_user'],
                credentials['api_key'],
            )

    def _show_login_widget(self):
        '''Show the login widget.'''
        self._login_overlay = ftrack_connect.ui.widget.overlay.CancelOverlay(
            self._login_widget, message='<h2>Signing in<h2/>'
        )

        self._login_overlay.hide()
        self.setCentralWidget(self._login_widget)
        self._login_widget.login.connect(self._login_overlay.show)
        self._login_widget.login.connect(self.loginWithCredentials)
        self.loginError.connect(self._login_widget.loginError.emit)
        self.loginError.connect(self._login_overlay.hide)
        self.focus()

        # Set focus on the login widget to remove any focus from its child
        # widgets.
        self._login_widget.setFocus()
        self._login_overlay.hide()

    def _get_api_plugin_paths(self):
        api_plugin_paths = []

        for apiPluginPath in os.environ.get(
            'FTRACK_EVENT_PLUGIN_PATH', ''
        ).split(os.pathsep):
            if apiPluginPath and apiPluginPath not in api_plugin_paths:
                api_plugin_paths.append(os.path.expandvars(apiPluginPath))

        checked_plugins = []
        for plugin in self.plugins:
            # Always pick the
            if plugin['name'] in checked_plugins:
                continue
            if plugin['incompatible']:
                self.logger.warning(
                    f'Ignoring plugin that is incompatible: {plugin["path"]}'
                )
                continue
            checked_plugins.append(plugin['name'])
            api_plugin_paths.append(os.path.join(plugin['path'], 'hook'))

        return api_plugin_paths

    def _setup_session(self, api_plugin_paths=None):
        '''Setup a new python API session.'''
        if hasattr(self, '_hub_thread'):
            self._hub_thread.cleanup()

        if api_plugin_paths is None:
            api_plugin_paths = self._get_api_plugin_paths()
        try:
            session = ftrack_api.Session(
                auto_connect_event_hub=True, plugin_paths=api_plugin_paths
            )
        except Exception as error:
            raise ftrack_connect.error.ParseError(error)

        # Need to reconfigure logging after session is created.
        ftrack_connect.utils.log.configure_logging(
            'ftrack_connect', level=self._log_level, notify=False
        )

        # Listen to events using the new API event hub. This is required to
        # allow reconfiguring the storage scenario.
        self._hub_thread = _event_hub_thread.NewApiEventHubThread(self)

        self._hub_thread.start(session)
        weakref.finalize(self._hub_thread, self._hub_thread.cleanup)

        ftrack_api._centralized_storage_scenario.register_configuration(
            session
        )

        # Initialize UsageTracker for connect
        set_usage_tracker(
            UsageTracker(
                session=session,
                default_data=dict(
                    app="Connect",
                    version=ftrack_connect.__version__,
                    os=platform.platform(),
                    python_version=platform.python_version(),
                ),
            )
        )

        return session

    def _report_session_setup_error(self, error):
        '''Format error message and emit loginError.'''
        msg = (
            u'\nAn error occured while starting ftrack-connect: <b>{0}</b>.'
            u'\nPlease check log file for more informations.'
            u'\nIf the error persists please send the log file to:'
            u' support@ftrack.com'.format(error)
        )
        self.loginError.emit(msg)

    def loginWithCredentials(self, url, username, apiKey):
        '''Connect to *url* with *username* and *apiKey*.

        loginError will be emitted if this fails.

        '''
        # Strip all leading and preceeding occurances of slash and space.
        url = url.strip('/ ')

        if not url:
            self.loginError.emit(
                'You need to specify a valid server URL, '
                'for example https://server-name.ftrackapp.com'
            )
            return

        if not 'http' in url:
            if url.endswith('ftrackapp.com'):
                url = 'https://' + url
            else:
                url = 'https://{0}.ftrackapp.com'.format(url)

        try:
            result = requests.get(
                url,
            )
        except requests.exceptions.RequestException:
            self.logger.exception('Error reaching server url.')
            self.loginError.emit(
                'The server URL you provided could not be reached.'
            )
            return

        if result.status_code != 200 or 'FTRACK_VERSION' not in result.headers:
            self.loginError.emit(
                'The server URL you provided is not a valid ftrack server.'
            )
            return

        # If there is an existing server thread running we need to stop it.
        if self._login_server_thread:
            self._login_server_thread.quit()
            self._login_server_thread = None

        # If credentials are not properly set, try to get them using a http
        # server.
        if not username or not apiKey:
            self._login_server_thread = _login_tools.LoginServerThread()
            self._login_server_thread.loginSignal.connect(self.loginSignal)
            self._login_server_thread.finished.connect(
                self._login_server_thread.deleteLater
            )
            self._login_server_thread.start(url)
            return

        # Set environment variables supported by the new API.
        os.environ['FTRACK_SERVER'] = url
        os.environ['FTRACK_API_USER'] = username
        os.environ['FTRACK_API_KEY'] = apiKey

        # Login using the new ftrack API.
        try:
            # Quick session to poll for settings, confirm credentials
            self._session = self._setup_session(api_plugin_paths='')
            self._assign_session_theme(self.theme())
        except Exception as error:
            self.logger.exception('Error during login:')
            self._report_session_setup_error(error)
            return

        # Store credentials since login was successful.
        self._save_credentials(url, username, apiKey)

        # Verify storage scenario before starting.
        if 'storage_scenario' in self.session.server_information:
            storage_scenario = self.session.server_information.get(
                'storage_scenario'
            )
            if storage_scenario is None:
                ftrack_api.plugin.discover(
                    self._get_api_plugin_paths(), [self.session]
                )
                # Hide login overlay at this time since it will be deleted
                self.logger.debug('Storage scenario is not configured.')
                scenario_widget = _scenario_widget.ConfigureScenario(
                    self.session
                )
                scenario_widget.configuration_completed.connect(
                    self._location_configuration_finished
                )
                self.setCentralWidget(scenario_widget)
                self.focus()
                self.loginSuccessSignal.emit()
                return

        # No change so build if needed
        self._location_configuration_finished(reconfigure_session=False)
        self.loginSuccessSignal.emit()

    def _location_configuration_finished(self, reconfigure_session=True):
        '''Continue connect setup after location configuration is done.'''
        if reconfigure_session:
            try:
                self.session.event_hub.disconnect(False)
            except ftrack_api.exception.EventHubConnectionError:
                # Maybe it wasn't connected yet.
                self.logger.exception('Failed to disconnect from event hub.')
                pass

        self._session = self._setup_session()

        try:
            self._configure_connect_and_discover_plugins()
        except Exception as error:
            self.logger.exception(u'Error during location configuration:')
            self._report_session_setup_error(error)
        else:
            self.focus()

        # Send verify startup event to verify that storage scenario is
        # working correctly.
        event = ftrack_api.event.base.Event(
            topic='ftrack.connect.verify-startup',
            data={
                'storage_scenario': self.session.server_information.get(
                    'storage_scenario'
                )
            },
        )
        results = self.session.event_hub.publish(event, synchronous=True)
        problems = [problem for problem in results if isinstance(problem, str)]
        if problems:
            msgBox = QtWidgets.QMessageBox(parent=self)
            msgBox.setIcon(QtWidgets.QMessageBox.Icon.Warning)
            msgBox.setText('\n\n'.join(problems))
            msgBox.exec_()

    def _configure_connect_and_discover_plugins(self):
        '''Configure connect and load plugins.'''

        self.tabPanel = _tab_widget.TabWidget()
        self.tabPanel.tabBar().setObjectName('application-tab-bar')
        self.setCentralWidget(self.tabPanel)

        self.session.event_hub.subscribe(
            'topic=ftrack.connect and source.user.username="{0}"'.format(
                self.session.api_user
            ),
            self._relay_event,
        )
        self.eventHubSignal.connect(self._onConnectTopicEvent)

        self.focus()

        # Listen to discover connect event and respond to let the sender know
        # that connect is running.
        self.session.event_hub.subscribe(
            'topic=ftrack.connect.discover and source.user.username="{0}"'.format(
                self.session.api_user
            ),
            lambda event: True,
        )
        self.session._configure_locations()

        self._discover_applications()  # Was ftrack-application-launcher

        self._configure_action_launcher_widget()  # Was external ftrack-connect action-launcher plugin

        self._configure_plugin_manager_widget()  # Was external ftrack-connect-plugin-manager plugin

        self._discover_connect_widgets()

    def _gather_plugins(self, plugin_directory, source_index=None):
        '''Return plugin data from *plugin_directory*.'''

        result = []
        if not plugin_directory:
            return result
        self.logger.debug(
            u'Searching {0!r} for plugin hooks.'.format(plugin_directory)
        )
        if os.path.isdir(plugin_directory):
            for candidate in get_plugins_from_path(plugin_directory):
                self.logger.debug(f'Checking candidate {candidate}.')
                candidate_path = os.path.join(plugin_directory, candidate)
                plugin_data = get_plugin_data(candidate_path)
                if not plugin_data:
                    continue
                if source_index >= 0:
                    plugin_data['source_index'] = source_index
                result.append(plugin_data)

        self.logger.debug(
            u'Found {0!r} plugin hooks in {1!r}.'.format(
                result, plugin_directory
            )
        )

        return result

    def _available_plugin_data_from_plugin_directories(self):
        '''Return a list of plugin data'''

        result = []
        i = 0
        for plugin_base_directory in PLUGIN_DIRECTORIES:
            current_dir_plugins = []
            for plugin in self._gather_plugins(
                plugin_base_directory, source_index=i
            ):
                # Append plugin if not already in more prioritized paths. - top plugin path takes preference
                found = False
                for existing_plugin in result:
                    if (
                        existing_plugin['name'].lower()
                        == plugin['name'].lower()
                    ):
                        found = True
                        break
                # Make sure we pick the compatible latest version of the plugin from the current folder
                for current_dir_plugin in current_dir_plugins:
                    if (
                        current_dir_plugin['name'].lower()
                        == plugin['name'].lower()
                    ):
                        if (
                            current_dir_plugin['incompatible']
                            and not plugin['incompatible']
                        ):
                            current_dir_plugins.remove(current_dir_plugin)
                            break
                        elif (
                            current_dir_plugin['deprecated']
                            and not plugin['incompatible']
                            and not plugin['deprecated']
                        ):
                            current_dir_plugins.remove(current_dir_plugin)
                            break
                        elif (
                            not plugin['incompatible']
                            and not plugin['deprecated']
                        ):
                            if (
                                current_dir_plugin['version']
                                < plugin['version']
                            ):
                                current_dir_plugins.remove(current_dir_plugin)
                                break
                        found = True
                        break
                if not found:
                    current_dir_plugins.append(plugin)
            result.extend(current_dir_plugins)
            i += 1
        return result

    def _discover_plugin_data_from_plugin_directories(self):
        '''Return a list of all plugin data from the plugin directories'''

        result = []
        i = 0
        for plugin_base_directory in PLUGIN_DIRECTORIES:
            result.extend(
                self._gather_plugins(plugin_base_directory, source_index=i)
            )
            i += 1
        return result

    def _relay_event(self, event):
        '''Relay all ftrack.connect events.'''
        self.eventHubSignal.emit(event)

    def _initialise_tray(self):
        '''Initialise and add application icon to system tray.'''
        self.trayMenu = self._create_tray_menu()

        self.tray = QtWidgets.QSystemTrayIcon(self)

        self.tray.setContextMenu(self.trayMenu)

    def _initialise_menu_bar(self):
        '''Initialise and add connect widget to widgets menu.'''

        self.menu_bar = QtWidgets.QMenuBar(self.centralWidget())
        self.setMenuWidget(self.menu_bar)
        widget_menu = self.menu_bar.addMenu('Widgets')
        self.menu_widget = widget_menu
        self.menu_bar.setVisible(False)

    def _create_tray_menu(self):
        '''Return a menu for system tray.'''
        menu = QtWidgets.QMenu(self.centralWidget())

        logoutAction = QAction('Log Out && Quit', self, triggered=self.logout)

        quitAction = QAction(
            'Quit', self, triggered=QtWidgets.QApplication.quit
        )

        focusAction = QAction('Open', self, triggered=self.focus)

        openPluginDirectoryAction = QAction(
            'Open plugin directory',
            self,
            triggered=self._open_default_plugin_directory,
        )

        aboutAction = QAction('About', self, triggered=self._show_about)

        alwaysOnTopAction = QAction('Always on top', self)
        restartAction = QAction('Restart', self, triggered=self.restart)
        alwaysOnTopAction.setCheckable(True)
        alwaysOnTopAction.triggered[bool].connect(self._set_always_on_top)

        menu.addAction(aboutAction)
        menu.addSeparator()
        menu.addAction(focusAction)
        menu.addAction(alwaysOnTopAction)
        menu.addSeparator()

        menu.addAction(openPluginDirectoryAction)
        menu.addSeparator()

        menu.addAction(logoutAction)
        menu.addSeparator()
        menu.addAction(restartAction)
        menu.addAction(quitAction)

        return menu

    def _discover_connect_widgets(self):
        '''Find and load connect widgets in search paths.'''

        event = ftrack_api.event.base.Event(topic=ConnectWidgetPlugin.topic)
        responses = self.session.event_hub.publish(event, synchronous=True)

        # Load icons
        load_fonts_resource()

        for plugin_class in self._builtin_widget_plugins + responses:
            widget_plugin = None
            try:
                widget_plugin = plugin_class(self.session)

            except Exception:
                self.logger.exception(
                    msg='Error while loading plugin : {}'.format(widget_plugin)
                )
                continue

            if not isinstance(widget_plugin, ConnectWidget):
                self.logger.warning(
                    'Widget {} is not a valid ConnectWidget'.format(
                        widget_plugin
                    )
                )
                continue
            try:
                identifier = widget_plugin.getIdentifier()
                if not self._widget_plugin_instances.get(identifier):
                    self._widget_plugin_instances[identifier] = widget_plugin
                else:
                    self.logger.debug(
                        'Widget {} already registered'.format(identifier)
                    )
                    continue

                self._add_plugin(widget_plugin)

            except Exception as error:
                self.logger.warning(
                    'Connect Widget Plugin "{}" could not be loaded. Reason: {}'.format(
                        widget_plugin.getName(), str(error)
                    )
                )

    def _route_event(self, event):
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
            pluginInstance = self._widget_plugin_instances[plugin]
        except KeyError:
            raise ftrack_connect.error.ConnectError(
                'Plugin "{0}" not found.'.format(plugin)
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

    def _on_fetch_plugins_callback(self, callback_fn):
        '''Call *callback_fn* with list of active Connect plugins'''
        callback_fn(self.plugins)

    def _on_widget_request_application_focus_callback(self, widget):
        '''Switch tab to *widget* and bring application to front.'''
        self.tabPanel.setCurrentWidget(widget)
        self.focus()

    def _on_widget_request_acpplication_close_callback(self, widget):
        '''Hide application upon *widget* request.'''
        self.hide()

    def _add_plugin(self, plugin, name=None):
        '''Add *plugin* in new tab with *name* and *identifier*.

        *plugin* should be an instance of :py:class:`ApplicationPlugin`.

        *name* will be used as the label for the tab. If *name* is None then
        plugin.getName() will be used.

        *identifier* will be used for routing events to plugins. If
        *identifier* is None then plugin.getIdentifier() will be used.

        '''
        if name is None:
            name = plugin.getName()

        try:
            icon = qta.icon(plugin.icon)
        except Exception:
            icon = QtGui.QIcon(plugin.icon)

        self.tabPanel.addTab(plugin, icon, name)

        # Connect standard plugin events.
        plugin.fetchPlugins.connect(self._on_fetch_plugins_callback)
        plugin.requestApplicationFocus.connect(
            self._on_widget_request_application_focus_callback
        )
        plugin.requestApplicationClose.connect(
            self._on_widget_request_acpplication_close_callback
        )
        plugin.requestConnectRestart.connect(self.restart)

        plugin.refresh()

        self.logger.debug(f'Plugin {name}({plugin.__class__.__name__}) added')

    def _remove_plugin(self, plugin):
        '''Remove plugin registered with *identifier*.

        Raise :py:exc:`KeyError` if no plugin with *identifier* has been added.

        '''
        identifier = plugin.getIdentifier()
        registered_plugin = self._widget_plugin_instances.get(identifier)

        if registered_plugin is None:
            self.logger.warning(
                'No plugin registered with identifier "{0}".'.format(
                    identifier
                )
            )
            return

        index = self.tabPanel.indexOf(registered_plugin)
        self.tabPanel.removeTab(index)

    def focus(self):
        '''Focus and bring the window to top.'''
        self.activateWindow()
        self.show()
        self.raise_()

    def _set_always_on_top(self, state):
        '''Set the application window to be on top'''
        if state:
            self.setWindowFlags(
                self.windowFlags() | QtCore.Qt.WindowType.WindowStaysOnTopHint
            )
        else:
            self.setWindowFlags(
                self.windowFlags() & ~QtCore.Qt.WindowType.WindowStaysOnTopHint
            )
        self.focus()

    def _show_about(self):
        '''Display window with about information.'''
        from ftrack_connect.plugin_manager import PluginManager
        from ftrack_connect.plugin_manager.processor import ROLES, STATUSES

        self.focus()

        aboutDialog = _about.AboutDialog(self)

        environment_data = os.environ.copy()
        environment_data.update(
            {
                'PLATFORM': platform.platform(),
                'PYTHON_VERSION': platform.python_version(),
            }
        )

        debug_information = {'environment': environment_data, 'widgets': []}

        # Provide debug information from application launcher
        if self._application_launcher:
            debug_information[
                'application_launcher'
            ] = self._application_launcher.get_debug_information()

        # Provide information from builtin widget plugins.
        for plugin in self._widget_plugin_instances:
            if isinstance(plugin, ConnectWidget):
                debug_information['widgets'].append(
                    plugin.get_debug_information()
                )

        connect_version_data = {
            'name': 'ftrack connect',
            'version': ftrack_connect.__version__,
            'core': True,
            'debug_information': debug_information,
        }

        result = [connect_version_data]

        # Append all available plugins
        for plugin in self._discovered_plugins:
            result.append(copy.deepcopy(plugin))

        # Gather information about API versions and other
        # plugin hooks through event, append or add to result

        try:
            event = ftrack_api.event.base.Event(
                topic='ftrack.connect.plugin.debug-information'
            )

            raw_responses = self.session.event_hub.publish(
                event, synchronous=True
            )

            responses = []
            for response in raw_responses:
                if isinstance(response, dict):
                    responses.append(response)
                elif isinstance(response, list):
                    responses.extend(response)
            for response in responses:
                if response.get('core'):
                    result.append(response)
                    continue
                found = False
                for plugin_data in result:
                    if plugin_data['name'] == response['name']:
                        found = True
                        # Update information
                        plugin_data.update(response)
                        break
                if not found:
                    result.append(response)
        except Exception as error:
            self.logger.error(error)

        current_plugins_path = [plugin['path'] for plugin in self.plugins]
        # Highlight compatibility and source of plugins
        for plugin_data in result:
            if plugin_data.get('core') or 'path' not in plugin_data:
                continue
            tags = []
            if plugin_data.get('incompatible'):
                tags.append('Incompatible')
            elif plugin_data.get('deprecated'):
                tags.append('Deprecated')
            if plugin_data['path'] not in current_plugins_path:
                tags.append('Ignored')
            plugin_data['tags'] = ",".join(tags)

        sorted_version_data = sorted(result, key=itemgetter('name'))

        aboutDialog.setInformation(
            versionData=sorted_version_data,
            server=os.environ.get('FTRACK_SERVER', 'Not set'),
            user=self.session.api_user,
            widget_plugins=self._widget_plugin_instances,
        )

        aboutDialog.exec_()

    def _open_default_plugin_directory(self):
        '''Open default plugin directory in platform default file browser.'''

        try:
            create_target_plugin_directory(PLUGIN_DIRECTORIES[0])
        except OSError:
            messageBox = QtWidgets.QMessageBox(parent=self)
            messageBox.setIcon(QtWidgets.QMessageBox.Icon.Warning)
            messageBox.setText(
                u'Could not open or create default plugin '
                u'directory: {0}.'.format(get_default_plugin_directory())
            )
            messageBox.exec_()
            return

        open_directory(get_default_plugin_directory())

    def _discover_applications(self):
        '''Walk through Connect plugins and pick up application launcher
        configuration files.'''
        launcher_config_paths = []

        self.logger.debug(
            f'Discovering applications launcher configs based on'
            f' {len(self.plugins)} plugins.'
        )

        for connect_plugin_path in [plugin['path'] for plugin in self.plugins]:
            launcher_config_path = os.path.join(connect_plugin_path, 'launch')
            if os.path.isdir(launcher_config_path):
                launcher_config_paths.append(launcher_config_path)

        # Create store containing launchable applications.
        self._application_launcher = DiscoverApplications(
            self.session, launcher_config_paths
        )
        self._application_launcher.register()

    def _configure_action_launcher_widget(self):
        '''Append action launcher widget to list of build in
        plugins to add on discovery together with user plugins.'''

        from ftrack_connect.action_launcher import ActionLauncherWidget

        # Add together with discovered widgets
        self._builtin_widget_plugins.append(ActionLauncherWidget)

    def _configure_plugin_manager_widget(self):
        '''Append plugin manager widget to list of build in
        plugins to add on discovery together with user plugins.'''

        from ftrack_connect.plugin_manager import PluginManager

        if (
            os.environ.get('FTRACK_CONNECT_DISABLE_PLUGIN_MANAGER') or ''
        ).lower() not in [
            'true',
            '1',
        ]:
            # Add together with discovered widgets
            self._builtin_widget_plugins.append(PluginManager)
        else:
            self.logger.warning(
                'Plugin manager disabled by user environment variable.'
            )

    def closeEvent(self, event):
        ''' ' Quit application when main window is closed, and no tray'''
        if not self.tray:
            sys.exit(0)
