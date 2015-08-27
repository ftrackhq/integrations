# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

from PySide import QtGui, QtWebKit, QtCore
import hiero.core

import ftrack

from ftrack_connect.connector import PersistentCookieJar, HelpFunctions


class Ui_WebView(object):
    '''Webview UI.'''

    def setupUi(self, WebView):
        '''Setup UI for *WebView*.'''
        WebView.setObjectName('WebView')
        WebView.resize(688, 555)
        self.horizontalLayout = QtGui.QHBoxLayout(WebView)
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout.setObjectName('horizontalLayout')
        self.WebViewView = QtWebKit.QWebView(WebView)
        font = QtGui.QFont()
        font.setFamily('Anonymous Pro')
        self.WebViewView.setFont(font)
        self.WebViewView.setUrl(QtCore.QUrl('about:blank'))
        self.WebViewView.setObjectName('WebViewView')
        self.horizontalLayout.addWidget(self.WebViewView)

        self.retranslateUi(WebView)
        QtCore.QMetaObject.connectSlotsByName(WebView)

    def retranslateUi(self, WebView):
        '''Translate text for *WebView*.'''
        WebView.setWindowTitle(
            QtGui.QApplication.translate(
                'WebView', 'Form', None, QtGui.QApplication.UnicodeUTF8
            )
        )


class WebPage(QtWebKit.QWebPage):
    '''WebPage widget.'''

    def javaScriptConsoleMessage(self, msg, line, source):
        '''Print javascript console message.'''
        print '%s line %d: %s' % (source, line, msg)


# TODO: Remove this widget and refactor Maya plugin to use WebView.
class WebViewWidget(QtGui.QWidget):
    '''Webview widget class.'''

    def __init__(self, parent, task=None):
        '''Instansiate web view widget.'''
        QtGui.QWidget.__init__(self, parent)
        self.ui = Ui_WebView()
        self.ui.setupUi(self)

        self.webPage = WebPage()
        self.persCookieJar = PersistentCookieJar(self)
        self.persCookieJar.load()

        proxy = HelpFunctions.getFtrackQNetworkProxy()
        if proxy:
            self.webPage.networkAccessManager().setProxy(proxy)

        self.ui.WebViewView.setPage(self.webPage)

    def sslErrorHandler(self, reply, errorList):
        '''Handle ssl error.'''
        reply.ignoreSslErrors()

    def setUrl(self, url):
        '''Set web view url to *url*.'''
        self.ui.WebViewView.load(QtCore.QUrl(url))


class WebView(QtGui.QFrame):
    '''Display information about selected entity.'''

    def __init__(self, parent=None, url=None):
        '''Initialise WebView with *parent* and *url*'''
        super(WebView, self).__init__(parent)
        self.setMinimumHeight(400)
        self.setSizePolicy(
            QtGui.QSizePolicy(
                QtGui.QSizePolicy.Expanding,
                QtGui.QSizePolicy.Expanding
            )
        )

        layout = QtGui.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.setLayout(layout)

        self._webView = QtWebKit.QWebView()
        layout.addWidget(self._webView)

        self.setWindowTitle(self._display_name)
        self.setObjectName(self._identifier)

        self.set_url(url)

    def set_url(self, url):
        '''Load *url* and display result in web view.'''
        self._webView.load(QtCore.QUrl(url))

    def get_url(self):
        '''Return current url.'''
        url = self._webView.url().toString()
        if url in ('about:blank', ):
            return None

        return url