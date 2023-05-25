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

    QWebEngineView       _webNavigationWidget;
    QWebEngineView       _webActionWidget;

    QWidget         _titleNavigationWidget;
    QWidget         _titleActionWidget;

    bool           _firstRender;
    bool           _isHidden;
    bool           _debug;
    bool           _showPanelsOnStartup;
    
    
    string          _tmpFolder;
    string          _filePath;
    string          _ftrackUrl;
    string          _token;
    
    
    string[]        _doUpload;
    int[]           _annotatedFrames;
    
    int             _currentSource;
    
    
    python.PyObject _pyFilePath;
    python.PyObject _pyUUID;
    python.PyObject _create_component;
    python.PyObject _upload_component;

    python.PyObject _pyApi;
    python.PyObject _apiObject;

    method: pprint(void;string msg)
    {   
        if(_debug){
            print (msg + "\n");
        }
    }
    
    method: callApi (string; string action, string params) {
        pprint("Call to ftrack python api: %s" % action);
        pprint("With params: %s" % params);
        
        _apiObject = python.PyObject_GetAttr (_pyApi, action);
        return to_string(python.PyObject_CallObject (_apiObject, params));

    }

    method: generateUrl (string; string params, string name)
    {

        if(params eq nil) {
            params = "None";
        }
        
        if (name == "review_navigation") {
            return callApi("getNavigationURL", params);
        }
        
        if (name == "review_action") {
            return callApi("getActionURL", params);
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

    method: viewLoaded (void; QWidget view, bool ok)
    {
        view.setMaximumWidth(16777215);
        view.setMinimumWidth(0);
        view.setMaximumHeight(16777215);
        view.setMinimumHeight(250);
    }

    \: makeit (QObject;)
    {
        let Form = QWidget(mainWindowWidget(), Qt.Widget);
        let verticalLayout = QVBoxLayout(Form);
        verticalLayout.setSpacing(0);
        verticalLayout.setContentsMargins(4, 4, 4, 4);
        verticalLayout.setObjectName("verticalLayout");

        let webView = QWebEngineView(Form);
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
    
    method: showPanelsOnStartupToggle (void; Event event) {
        if(!_showPanelsOnStartup) {
            commands.writeSetting("ftrack", "showPanelsOnStartUp", SettingsValue.Bool(true));
            _showPanelsOnStartup = true;
            pprint("show on startup: %s" % _showPanelsOnStartup);
        }
        else {
            commands.writeSetting("ftrack", "showPanelsOnStartUp", SettingsValue.Bool(false));
            _showPanelsOnStartup = false;
            pprint("show on startup: %s" % _showPanelsOnStartup);
        }
    }
    
    method: showPanelsOnStartupState(int;) {
        pprint("show on startup: %s" % _showPanelsOnStartup);
        if(_showPanelsOnStartup) then CheckedMenuState else UncheckedMenuState;
    }
    
    method: panelState(int;) {
        pprint("Panels: %s" % _isHidden);
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
        if (_webNavigationWidget neq nil) _webNavigationWidget.page().setHtml("", qt.QUrl());
        if (_webActionWidget neq nil) _webActionWidget.page().setHtml("", qt.QUrl());
        
    }
    
    method: FtrackMode (FtrackMode; string name)
    {
        let SettingsValue.Bool _showPanelsOnStartUpBool = commands.readSetting(
            "ftrack", "showPanelsOnStartUp", SettingsValue.Bool(true)
        );
        _showPanelsOnStartup = _showPanelsOnStartUpBool;
        let SettingsValue.Bool _debugBool = commands.readSetting(
            "ftrack", "debug", SettingsValue.Bool(false)
        );
        _debug = _debugBool;

        init(name,
        [ ("before-session-deletion", shutdown, "") ],
        nil,
        Menu {
             {"ftrackReview", Menu {
                     {"Toggle panels", ftrackToggle, "control shift t",panelState},
                     {"Preferences", Menu {
                            {"Debug print", debugToggle, "control shift d",debugPrintState},
                            {"Show panels on startup", showPanelsOnStartupToggle, "", showPanelsOnStartupState},
                        }
                     },
                 }
             }
        });
        commands.sendInternalEvent("key-down--`");
        _drawOnEmpty  = true;
        _firstRender  = true;
        
        _dockActionWidget = nil;

        app_utils.bind("key-down--control--T", ftrackToggle, "Toggle ftrackReview panels");
        app_utils.bind("key-down--control--D", debugToggle, "Toggle ftrackReview debug prints");
        
        if (_showPanelsOnStartup) {
            _isHidden = false;
            initUi();
        }
        else {
            _isHidden = true;
        }
    }

    method: createActionWindow(void;)
    {
        if (_dockActionWidget eq nil) {
            let title = "",
            url = "",
            showTitle = bool("false"),
            showProg  = bool("false"),
            startSize = int ("500");

            url  = generateUrl(commandLineFlag("params", nil), "review_action");

            _dockActionWidget = QDockWidget(title, mainWindowWidget(), Qt.Widget);
            
            _baseActionWidget = makeit();
            
            _webActionWidget = _baseActionWidget.findChild("webView");
            connect(_webNavigationWidget, QWebEngineView.loadFinished, viewLoaded(_baseActionWidget,));

            _webActionWidget.load(QUrl(url));

            javascriptMuExport(_webActionWidget.page());

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

    method: initUi(void;)
    {
    if (_firstRender)
    {
        //BIND EVENTS
        app_utils.bind("ftrack-event", ftrackEvent, "Update action window");
        app_utils.bind("ftrack-timeline-loaded", createActionWindow, "User is logged in, create action window");

        app_utils.bind("ftrack-toggle-floating", toggleFloating, "Toggle floating panel");

        app_utils.bind("ftrack-upload-frame", ftrackExportAll, "Upload frame to FTrack");
        app_utils.bind("ftrack-upload-frames", ftrackExportAll, "Upload all annotated frames to FTrack");
        app_utils.bind("frame-changed", frameChanged, "New frame");
        app_utils.bind("ftrack-changed-group",navGroupChanged,"New group selected");

        //SETUP PYTHON API
        _pyApi    = python.PyImport_Import ("ftrack_rv_api");
        _pyFilePath     = python.PyObject_GetAttr (_pyApi, "ftrackFilePath");
        _pyUUID         = python.PyObject_GetAttr (_pyApi, "ftrackUUID");
        _create_component = python.PyObject_GetAttr(_pyApi, "create_component");
        _upload_component = python.PyObject_GetAttr(_pyApi, "upload_component");

        _firstRender = false;
        _currentSource = -1;

        _ftrackUrl  = commandLineFlag("ftrackUrl", nil);
        if (_ftrackUrl eq nil) {
            _ftrackUrl = getenv("FTRACK_SERVER");
        }

        let url = "";

        url  = generateUrl(commandLineFlag("params", nil), "review_navigation");

        if (url == "") {
            let noServer = path.join(supportPath("ftrack", "ftrack"), "noserver.html");
            let urlPrefix = if (runtime.build_os() == "WINDOWS") then "file:///" else "file://";
            url = urlPrefix + noServer;
        }

        let title = "",
        showTitle = bool("false"),
        showProg  = bool("false"),
        startSize = int ("270");


        _dockNavigationWidget = QDockWidget(title, mainWindowWidget(), Qt.Widget);
        
        _baseNavigationWidget = makeit();
        
        _webNavigationWidget     = _baseNavigationWidget.findChild("webView");
        connect(_webNavigationWidget, QWebEngineView.loadFinished, viewLoaded(_baseNavigationWidget,));

        _webNavigationWidget.load(QUrl(url));

        javascriptMuExport(_webNavigationWidget.page());

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

        mainWindowWidget().show();
    }
    }
        
    method: ftrackEvent (void; Event event)
    {
        
        try {
            _webNavigationWidget.page().runJavaScript("FT.updateFtrack(\"" + event.contents() + "\")");
        }
        catch (...)
        {
            nil;
        }

        try {
            _webActionWidget.page().runJavaScript("FT.updateFtrack(\"" + event.contents() + "\")");
        }
        catch (...)
        {
            nil;
        }
            
        
    }

    method: frameChanged (void;Event event) {
        
        let source  = int(regex.smatch("[a-zA-Z]+([0-9]+)", sourcesAtFrame(frame())[0]).back());
        if (_currentSource != source) {
            _currentSource = source;
            string data_string = "{\"type\":\"changedGroup\",\"index\":\"" + _currentSource + "\"}";
            byte[] data = encoding.string_to_utf8 (data_string);
            data = encoding.to_base64 ( data ); 
            _webNavigationWidget.page().runJavaScript("FT.updateFtrack(\"" + encoding.utf8_to_string( data ) + "\")");
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
            initUi(); // initUi checks if it has been called already...
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
            commands.writeSetting("ftrack", "debug", SettingsValue.Bool(false));
        }
        else {
            _debug = true;
            commands.writeSetting("ftrack", "debug", SettingsValue.Bool(true));
        }
        
        pprint ("Debug print: " + _debug);
    }
    
    method: uploadAll(void;) {
        pprint("Uploading all annotated frames");

        for_index (i; _doUpload)
        {   
            upload_annotation(_doUpload[i], _annotatedFrames[i]);
        }
    }
    
    method: uploadingCount (void;string count) {
        string data_string = "{\"type\":\"uploadCount\",\"count\":\"" + count + "\"}";
        byte[] data = encoding.string_to_utf8 (data_string);
        data = encoding.to_base64 ( data ); 
        _webActionWidget.page().runJavaScript("FT.updateFtrack(\"" + encoding.utf8_to_string( data ) + "\")");
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
            
            if (i > 0) print(timestr, ",");
            print(timestr, "%d" % f);
        }
        _doUpload = tmpUpload;
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
            pprint("Exporting Annotated Frames\n");
            rvio("Export Annotated Frames", args, uploadAll);
        }
    }

    /** 
     * Upload a single annotation saved as *filename*.
     *
     * Creates a component, adds the component to the note form and then
     * adds the component to the ftrack.server location.
     */
    method: upload_annotation(void; string filename, int frame) {
        pprint("Uploading file: %s" % filename);

        string encoded_args = "{\"file_name\":\"" + filename + "\",\"frame\":\"" + frame + "\"}";
        string component_id = to_string(python.PyObject_CallObject(_create_component, encoded_args));
        pprint("Created component: %s" % component_id);
        on_upload_started(component_id);

        python.PyObject_CallObject(_upload_component, component_id);
        pprint("Upload complete");
        on_upload_complete(component_id);
    }

    /** Update ftrack when upload has started. */
    method: on_upload_started(void; string component_id) {
        string data_string = "{\"type\": \"uploadStarted\", \"attachment\": \"" + component_id + "\"}";
        _update_ftrack(data_string);
    }

    /** Update ftrack when upload has completed. */
    method: on_upload_complete(void; string component_id) {
        string data_string = "{\"type\": \"uploadEnded\", \"id\": \"" + component_id + "\"}";
        _update_ftrack(data_string);
    }

    /** Update ftrack with json-formatedd *data_string*. */
    method: _update_ftrack(void; string data_string) {
        byte[] data = encoding.string_to_utf8(data_string);
        data = encoding.to_base64(data);
        _webActionWidget.page().runJavaScript("FT.updateFtrack(\"" + encoding.utf8_to_string( data ) + "\")");
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
