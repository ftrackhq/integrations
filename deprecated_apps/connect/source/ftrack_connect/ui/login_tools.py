# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import traceback
from http.server import BaseHTTPRequestHandler, HTTPServer
import urllib.parse
import webbrowser
import functools
import logging

try:
    from PySide6 import QtCore
except ImportError:
    from PySide2 import QtCore

logger = logging.getLogger(__name__)


class LoginServerHandler(BaseHTTPRequestHandler):
    '''Login server handler.'''

    def __init__(self, login_callback, *args, **kw):
        '''Initialise handler.'''
        self.login_callback = login_callback
        BaseHTTPRequestHandler.__init__(self, *args, **kw)

    def do_GET(self):
        '''Override to handle requests ourselves.'''
        try:
            parsed_path = urllib.parse.urlparse(self.path)
            query = parsed_path.query

            api_user = None
            api_key = None
            login_credentials = None
            if 'api_user' and 'api_key' in query:
                login_credentials = urllib.parse.parse_qs(query)
                api_user = login_credentials['api_user'][0]
                api_key = login_credentials['api_key'][0]
                message = """
                    <html>
                        <style type="text/css">
                            body {{
                                max-width: 400px;
                                margin: 30px auto;
                                font-family: 'Roboto', 'Open Sans', 'Droid Sans', Arial, Helvetica, sans-serif;
                                text-align: center;
                            }}
    
                            h1 {{
                                font-size: 20px;
                                font-weight: medium;
                                margin: 20px 0;
                            }}
    
                            p {{
                                color: #999;
                                margin: 30px 10px;
                            }}
                        </style>
                    <body>
                        <h1>Sign in to ftrack connect was successful</h1>
                        <p>
                            You signed in with username <em>{0}</em> and can now
                            close this window.
                        </p>
                    </body>
                    </html>
                """.format(
                    api_user
                )
            else:
                message = '<h1>Failed to sign in</h1>'

            self.send_response(200)
            self.end_headers()
            self.wfile.write(message.encode())

            if login_credentials:
                self.login_callback(api_user, api_key)
        except:
            logger.warning(traceback.format_exc())
            logger.exception(
                'An internal error occurred when handling request.'
            )
            self.send_response(500)
            self.end_headers()


class LoginServerThread(QtCore.QThread):
    '''Login server thread.'''

    # Login signal.
    loginSignal = QtCore.Signal(object, object, object)

    def start(self, url):
        '''Start thread.'''
        self.url = url
        super(LoginServerThread, self).start()

    def _handle_login(self, api_user, api_key):
        '''Login to server with *api_user* and *api_key*.'''
        self.loginSignal.emit(self.url, api_user, api_key)

    def run(self):
        '''Listen for events.'''
        import getpass
        import socket

        username = getpass.getuser()
        hostname = socket.gethostname()

        self._server = HTTPServer(
            ('localhost', 0),
            functools.partial(LoginServerHandler, self._handle_login),
        )
        webbrowser.open_new_tab(
            '{0}/user/api_credentials?identifier=ftrack-connect-{1}@{2}&redirect_url=http://localhost:{3}'.format(
                self.url, username, hostname, self._server.server_port
            )
        )
        logger.debug(f'Started login server @ port {self._server.server_port}')
        self._server.handle_request()
