module: ftrack {
use rvtypes;
use commands;
use extra_commands;
use system;
use qt;
use io;
use export_utils;
use math_util;
require app_utils;
require python;


class: FtrackMode : MinorMode
{ 
    QDockWidget    _dockNavigationWidget;
    QDockWidget    _dockActionWidget;

    QWidget        _baseNavigationWidget;
    QWidget        _baseActionWidget;

    QWebView       _webNavigationWidget;
    QWebView       _webActionWidget;


    QWidget         _titleNavigationWidget;
    QWidget         _titleActionWidget;

    QNetworkAccessManager _networkAccessManager;
    bool           _firstRender;
    bool           _isHidden;
    bool           _debug;
    
    
    string          _tmpFolder;
    string          _filePath;
    string          _attachmentId;
    string          _ftrackUrl;
    string          _token;
    
    
    string[]        _doUpload;
    int[]           _annotatedFrames;
    string[]        _attachmentIds;
    
    int             _currentSource;
    
    
    python.PyObject _pyGenerateUrl;
    python.PyObject _pyFilePath;
    python.PyObject _pyUUID;
    python.PyObject _getAttachmentId;
    
    python.PyObject _pyApi;
    python.PyObject _apiObject;

    method: pprint(void;string msg)
    {   
        if(_debug){
            print (msg + "\n");
        }
    }
    
    method: callApi (void; string action, string params) {
        pprint("Call to ftrack python api: %s" % action);
        pprint("With params: %s" % params);
        
        _apiObject = python.PyObject_GetAttr (_pyApi, action);

        python.PyObject_CallObject (_apiObject, params);
    }

    method: generateUrl (string; string params)
    {

        if(params neq nil) {
            return to_string(python.PyObject_CallObject (_pyGenerateUrl, params));
        }
        
        
        return "";
    }

    method: getFilePath(string;string id)
    {
        return to_string(python.PyObject_CallObject (_pyFilePath,id));
    }
    
    method: uuid()
    {
        return to_string(python.PyObject_CallObject (_pyUUID,""));
    }
    
    method: getAttachmentId(string;string s)
    {
        return to_string(python.PyObject_CallObject (_getAttachmentId,s));
    }

    method: viewLoaded (void; QWidget view, bool ok)
    {
        view.setMaximumWidth(16777215);
        view.setMinimumWidth(0);
        view.setMaximumHeight(16777215);
        view.setMinimumHeight(0);
    }

    \: makeit (QObject;)
    {
        let Form = QWidget(mainWindowWidget(), Qt.Widget);
        let verticalLayout = QVBoxLayout(Form);
        verticalLayout.setSpacing(0);
        verticalLayout.setContentsMargins(4, 4, 4, 4);
        verticalLayout.setObjectName("verticalLayout");

        let webView = QWebView(Form);
        webView.setObjectName("webView");
        verticalLayout.addWidget(webView);
        return Form;
    }
    
    method: hidePanels(void;)
    {
        if (_baseNavigationWidget neq nil) _baseNavigationWidget.hide();
        if (_dockNavigationWidget neq nil) _dockNavigationWidget.hide();

        if (_baseActionWidget neq nil) _baseActionWidget.hide();
        if (_dockActionWidget neq nil) _dockActionWidget.hide();
        
    }
    method: showPanels(void;)
    {
        if (_baseNavigationWidget neq nil) _baseNavigationWidget.show();
        if (_dockNavigationWidget neq nil) _dockNavigationWidget.show();

        if (_baseActionWidget neq nil) _baseActionWidget.show();
        if (_dockActionWidget neq nil) _dockActionWidget.show();
    }
    
    method: panelState(int;) {
        pprint("Panels: %s" % _debug);
        if(_isHidden) then UncheckedMenuState else CheckedMenuState;
    }
    
    method: debugPrintState(int;) {
        pprint("Debug: %s" % _debug);
        if(_debug) then CheckedMenuState else UncheckedMenuState;
    }

    method: toggleFloating (void; Event event) {

        int index = int(event.contents());
        QDockWidget dockWidget;
        QWidget titleWidget;

        if(index == 3) {
            dockWidget = _dockNavigationWidget;
            titleWidget = _titleNavigationWidget;
        }
        else {
            dockWidget = _dockActionWidget;
            titleWidget = _titleActionWidget;   
        }

        if(dockWidget.floating()) {
            dockWidget.setFloating(false);
        }
        else {
            dockWidget.setFloating(true);
        }
        
        toggleTitleBar(dockWidget, titleWidget, true);

    }


    method: toggleTitleBar (void;QDockWidget dockWidget, QWidget titleWidget, bool ok) {

        if(!dockWidget.floating()) {
            dockWidget.setTitleBarWidget(QWidget(mainWindowWidget(), 0));
        }
        else {
            dockWidget.setTitleBarWidget(titleWidget);
        }
    }

    method: shutdown (void; Event event)
    {
        event.reject();
        if (_webNavigationWidget neq nil) _webNavigationWidget.page().mainFrame().setHtml("", qt.QUrl());
        if (_webActionWidget neq nil) _webActionWidget.page().mainFrame().setHtml("", qt.QUrl());
        
    }
    
    method: FtrackMode (FtrackMode; string name)
    {
        _debug = true;

        init(name,
        [ ("before-session-deletion", shutdown, "") ],
        nil,
        Menu {
             {"ftrackReview", Menu {
                     {"Toggle panels", ftrackToggle, "control shift t",panelState},
                     {"Developer", Menu {
                            {"Debug print", debugToggle, "control shift d",debugPrintState},    
                        }
                     },
                 }
             }
        });
        commands.sendInternalEvent("key-down--`");
        _networkAccessManager = QNetworkAccessManager(mainWindowWidget());
        _drawOnEmpty  = true;
        _firstRender  = true;
        
        _dockActionWidget = nil;

        //BIND EVENTS
        
        app_utils.bind("ftrack-event", ftrackEvent, "Update action window");
        app_utils.bind("ftrack-timeline-loaded", createActionWindow, "User is logged in, create action window");

        app_utils.bind("ftrack-toggle-floating", toggleFloating, "Toggle floating panel");

        app_utils.bind("ftrack-upload-frame", ftrackExportAll, "Upload frame to FTrack");
        app_utils.bind("ftrack-upload-frames", ftrackExportAll, "Upload all annotated frames to FTrack");
        app_utils.bind("frame-changed", frameChanged, "New frame");
        app_utils.bind("ftrack-changed-group",navGroupChanged,"New group selected");

        app_utils.bind("key-down--control--T", ftrackToggle, "Toggle ftrackReview panels");
        app_utils.bind("key-down--control--D", debugToggle, "Toggle ftrackReview debug prints");
        
        
        //SETUP PYTHON API
        _pyApi    = python.PyImport_Import ("ftrack_api");
        _pyGenerateUrl  = python.PyObject_GetAttr (_pyApi, "ftrackGenerateUrl");
        _pyFilePath     = python.PyObject_GetAttr (_pyApi, "ftrackFilePath");
        _pyUUID         = python.PyObject_GetAttr (_pyApi, "ftrackUUID");
        _getAttachmentId    = python.PyObject_GetAttr (_pyApi, "ftrackGetAttachmentId");
    }

    method: createActionWindow(void;)
    {
        if (_dockActionWidget eq nil) {
            let title = "",
            url = "",
            showTitle = bool("false"),
            showProg  = bool("false"),
            startSize = int ("500");

            let params  = generateUrl(commandLineFlag("params", nil));
            url = _ftrackUrl + "/widget?view=freview_action_v1&itemId=freview&controller=widget" + params;

            _dockActionWidget = QDockWidget(title, mainWindowWidget(), Qt.Widget);
            
            _baseActionWidget = makeit();
            
            _webActionWidget = _baseActionWidget.findChild("webView");
            connect(_webNavigationWidget, QWebView.loadFinished, viewLoaded(_baseActionWidget,));

            _webActionWidget.page().setNetworkAccessManager(_networkAccessManager);
            _webActionWidget.load(QUrl(url));

            javascriptMuExport(_webActionWidget.page().mainFrame());

            _dockActionWidget.setWidget(_baseActionWidget);

            _titleActionWidget = _dockActionWidget.titleBarWidget();
            if (!showTitle) _dockActionWidget.setTitleBarWidget(QWidget(mainWindowWidget(), 0));
            
            connect(_dockActionWidget, QDockWidget.topLevelChanged, toggleTitleBar(_dockActionWidget, _titleActionWidget,));
            
            _dockActionWidget.setFeatures(
                    QDockWidget.DockWidgetFloatable |
                    QDockWidget.DockWidgetMovable);

            mainWindowWidget().addDockWidget(Qt.RightDockWidgetArea, _dockActionWidget);


            _baseActionWidget.setMaximumWidth(startSize);
            _baseActionWidget.setMinimumWidth(startSize);
            
            _baseActionWidget.show();
            _dockActionWidget.show();  
        }
        
    }

    method: render(Event event)
    {
    event.reject();
    if (_firstRender)
    {

        _firstRender = false;
        _currentSource = -1;

        _ftrackUrl  = commandLineFlag("ftrackUrl", nil);
        let url = "";
        //setenv("FTRACK_SERVER","http://localhost:5005", true);
        if (_ftrackUrl eq nil) {
            try {
                _ftrackUrl = getenv("FTRACK_SERVER");
            }
            catch (...) {
                pprint ("No FTRACK_SERVER environment variable set");
            }
        }

        if (_ftrackUrl neq nil) {
            url = url + _ftrackUrl;
            let params  = generateUrl(commandLineFlag("params", nil));
            url = _ftrackUrl + "/widget?view=freview_nav_v1&itemId=freview&controller=widget" + params;
        } else {
            let noServer = path.join(supportPath("ftrack", "ftrack"), "noserver.html");
            let urlPrefix = if (runtime.build_os() == "WINDOWS") then "file:///" else "file://";
            url = urlPrefix + noServer;
        }
        //let qurl = QUrl("file:///Users/carlclaesson/Desktop/noserver.html");

        let title = "",
        showTitle = bool("false"),
        showProg  = bool("false"),
        startSize = int ("270");


        _dockNavigationWidget = QDockWidget(title, mainWindowWidget(), Qt.Widget);
        
        _baseNavigationWidget = makeit();
        
        _webNavigationWidget     = _baseNavigationWidget.findChild("webView");
        connect(_webNavigationWidget, QWebView.loadFinished, viewLoaded(_baseNavigationWidget,));

        _webNavigationWidget.page().setNetworkAccessManager(_networkAccessManager);

        _webNavigationWidget.load(QUrl(url));

        javascriptMuExport(_webNavigationWidget.page().mainFrame());

        _dockNavigationWidget.setWidget(_baseNavigationWidget);


        
        _titleNavigationWidget = _dockNavigationWidget.titleBarWidget();
        if (!showTitle) _dockNavigationWidget.setTitleBarWidget(QWidget(mainWindowWidget(), 0));
        
        connect(_dockNavigationWidget, QDockWidget.topLevelChanged, toggleTitleBar(_dockNavigationWidget, _titleNavigationWidget,));
        
        _dockNavigationWidget.setFeatures(
                QDockWidget.DockWidgetFloatable |
                QDockWidget.DockWidgetMovable);

        mainWindowWidget().addDockWidget(Qt.BottomDockWidgetArea, _dockNavigationWidget);

        _baseNavigationWidget.setMaximumHeight(startSize);
        _baseNavigationWidget.setMinimumHeight(startSize);
        
        _baseNavigationWidget.show();
        _dockNavigationWidget.show();  

        _isHidden = false; 
        mainWindowWidget().show();
        // mainWindowWidget().showMaximized();
        showConsole();
    }
    }
        
    method: ftrackEvent (void; Event event)
    {
        
        try {
            _webNavigationWidget.page().mainFrame().evaluateJavaScript("FT.updateFtrack(\"" + event.contents() + "\")");
        }
        catch (...)
        {
            nil;
        }

        try {
            _webActionWidget.page().mainFrame().evaluateJavaScript("FT.updateFtrack(\"" + event.contents() + "\")");
        }
        catch (...)
        {
            nil;
        }
            
        
    }

    method: uploadProgress (void; Event event) {
        pprint ("uploadProgress\n");
    }
    
    method: uploadDone (void; Event event) {
        pprint ("uploadDone\n");
        
        
        string data_string = "{\"type\":\"uploadEnded\",\"id\":\"" + getAttachmentId( event.contents() ) + "\"}";
        byte[] data = encoding.string_to_utf8 (data_string);
        data = encoding.to_base64 ( data );     
        
        _webActionWidget.page().mainFrame().evaluateJavaScript("FT.updateFtrack(\"" + encoding.utf8_to_string( data ) + "\")");
    }
    
    method: frameChanged (void;Event event) {
        
        let source  = int(regex.smatch("[a-zA-Z]+([0-9]+)", sourcesAtFrame(frame())[0]).back());
        if (_currentSource != source) {
            _currentSource = source;
            string data_string = "{\"type\":\"changedGroup\",\"index\":\"" + _currentSource + "\"}";
            byte[] data = encoding.string_to_utf8 (data_string);
            data = encoding.to_base64 ( data ); 
            _webNavigationWidget.page().mainFrame().evaluateJavaScript("FT.updateFtrack(\"" + encoding.utf8_to_string( data ) + "\")");
        }
        
        
    }
    
    method: navGroupChanged(void;Event event) {
        // TODO: Padd the name with zeros instead
        setViewNode("sourceGroup00000"+event.contents());
    }
    
    method: ftrackToggle (void; Event event)
    {
        if (_isHidden) {
            _isHidden = false;
            showPanels();
        }
        else {
            _isHidden = true;
            hidePanels();
        }

    }
    
    method: debugToggle (void; Event event)
    {
        if (_debug) {
            _debug = false;
        }
        else {
            _debug = true;
        }
        
        pprint ("Debug print: " + _debug);
    }
    
    method: uploadAll(void;) {
        for_index (i; _doUpload)
        {   
            pprint("Upload: " + _doUpload[i]);
            uploadOne(_doUpload[i],_annotatedFrames[i],_attachmentIds[i]);
        }
    }
    
    method: uploadingCount (void;string count) {
        string data_string = "{\"type\":\"uploadCount\",\"count\":\"" + count + "\"}";
        byte[] data = encoding.string_to_utf8 (data_string);
        data = encoding.to_base64 ( data ); 
        _webActionWidget.page().mainFrame().evaluateJavaScript("FT.updateFtrack(\"" + encoding.utf8_to_string( data ) + "\")");
    }    

    method: ftrackExportAll (void; Event event) {
        use io;
        osstream timestr;
         
        _token = event.contents();
        // Add all the frames and export
        // Generate filenames that are unique
        // set name eg. Frame_159_1.jpg,Frame_159_2.jpg
          
        _filePath = getFilePath("");
        string[] tmpUpload = {};
        string[] tmpIds = {};
        let _uuid = uuid();
               
        // Get all the annotated frames
        // Function
        int[] frames = {};
        
        if(event.name() == "ftrack-upload-frame") {
            frames.push_back(frame());
        } 
        else {
            frames = findAnnotatedFrames(); 
        }
        
        _annotatedFrames = frames;  
        
        
        for_index (i; frames)
        {
            let f = frames[i];
            let fpadd = "%04d" % f;
            tmpUpload.push_back("%s_%s.jpg" % (_uuid,fpadd));
            let id = uuid();
            startUploadSpinners(id);
            tmpIds.push_back(id);
            
            if (i > 0) print(timestr, ",");
            print(timestr, "%d" % f);
        }
        _doUpload = tmpUpload;
        _attachmentIds = tmpIds;
        string[] args = 
        {
            makeTempSession(), 
            "-o", "%s/%s_#.jpg" % (_filePath,_uuid), 
            "-t", string(timestr),
            "-overlay","frameburn","0.8","1.0","30.0"
        };
        pprint(_doUpload.size());
        uploadingCount(_doUpload.size());
        if (_doUpload.size() > 0) {
            rvio("Export Annotated Frames", args, uploadAll);
        }
    }
    
    method: startUploadSpinners(void;string id) {
        string data_string = "{\"type\":\"uploadStarted\",\"attachment\":\"" + id + "\"}";
        byte[] data = encoding.string_to_utf8 (data_string);
        data = encoding.to_base64 ( data );
        _webActionWidget.page().mainFrame().evaluateJavaScript("FT.updateFtrack(\"" + encoding.utf8_to_string( data ) + "\")");
    }
   
    
    method: uploadOne (void; string filename, int frame,string id)
    {
        
        
        pprint ("Upload event\n");
        // Set the upload URL
        string url = _ftrackUrl + "/attachment/imageUpload";
        string uploadToken = _token;
        let _attachmentId = id;
        string _fileName = "Frame_%s.jpg" % sourceFrame(frame);
        
        _filePath = "%s/%s" % (getFilePath(""),filename);
        //exportCurrentFrame(_filePath);
        
        
        let file  = io.ifstream (_filePath, io.stream.In | io.stream.Binary),
            bytes = io.read_all_bytes (file),
            b64   = encoding.to_base64 (bytes);


        string boundary = "00---------------------------7d03135102b8";

        string contents = "";
        contents += "--%s\r\nContent-Disposition: form-data; name=\"%s\"\r\n\r\n%s\r\n" % (boundary, "attachmentid", _attachmentId);
        contents += "--%s\r\nContent-Disposition: form-data; name=\"%s\"\r\n\r\n%s\r\n" % (boundary, "auth_token", uploadToken);
        contents += "--%s\r\nContent-Disposition: form-data; name=\"%s\"\r\n\r\n%s\r\n" % (boundary, "name", "file");
        contents += "--%s\r\n" % boundary;
        contents += "Content-Disposition: form-data; "; 

        contents += "name=\"file\"; ";

        contents += "filename=\"%s\"\r\n" % _fileName;
        contents += "Content-Type: image/jpeg\r\n";
        contents += "Content-Length: %s\r\n\r\n" % string(bytes.size());

        \: byteAppend (void; byte[] b, string s)
        {
            for (int i = 0; i < s.size(); ++i) b.push_back(byte(s[i]));

        }
        \: byteAppend (void; byte[] b, byte[] b2)
        {
            for (int i = 0; i < b2.size(); ++i) b.push_back(b2[i]);
        }

        byte[] finalBytes = byte[]();

        let start = theTime();

        byteAppend (finalBytes, contents);
        byteAppend (finalBytes, bytes);
        byteAppend (finalBytes, "\r\n--%s--\r\n\r\n" % boundary);

        [(string,string)] headers;

        headers = ("Connection", "close") : headers;
        headers = ("Content-Type", "multipart/form-data; boundary=%s" % boundary) : headers;
        headers = ("Content-Length", string(finalBytes.size())) : headers;
        headers = ("Accept-Encoding", "identity") : headers;

        app_utils.bind ("ftrack-upload-done", uploadDone);
        app_utils.bind ("ftrack-uploading", uploadProgress);

        httpPost (url, headers, finalBytes, "ftrack-upload-done", nil, "ftrack-uploading", true);  
    }
    
    

}

\: theMode (FtrackMode; )
{
    require rvui;
    FtrackMode m = rvui.minorModeFromName("webview");

    return m;
}

\: createMode (Mode;)
{
    return FtrackMode("webview");
}
}