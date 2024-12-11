/*
ftrack After Effects Framework integration CEP interface functions

Exposed by RPC call event to Python standalone host.

Copyright (c) 2024 ftrack
*/


// Util

/**
* Convert to forward slashes to fix issues with JSON encoding
*/
function exportPath(path) {
    return path.replace(/\\/g, "/");
}

/**
 * Convert to back slashes on windows
*/
function importPath(path) {
    if ($.os.indexOf("Windows") != -1)
        return path.replace(/\//g, "\\");
    else
        return path;
}

// Project

function hasProject() {
    return app.project?"true":"false";
}

function getProjectPath() {
    /*
     * Returns the path of the document, or an empty string if it has not been saved
    */
    try {
        return exportPath(app.project.file.fsName);
    } catch (e) {
        alert(e);
        return "Error: could not get project path: "+e+" Details: "+e.stack;
    }
}

function saveProject() {
    /*
     * Save the current project
     *
     * Note: Can't check if document is saved in aftereffects
    */
    try {
        app.project.save();
        return "true";
    } catch (e) {
        alert(e);
        return "Error: could not save project: "+e+" Details: "+e.stack;
    }
}

function saveProjectAs(temp_path) {
    /*
     * Saves the project to the given temp_path, return "true" if successful,
     * "false" otherwise. Support psd or psb format.
    */
    try {
        app.project.save(File(importPath(temp_path)));
        return "true";
    } catch (e) {
        alert(e);
        return "Error: could not save project to custom location: "+e+" Details: "+e.stack;
    }
}

function getOutputModuleTemplateNames(){
    /*
     * Return list of aviable Output Module templates
    */
    var currentOMName;
    var OMStringsPrefSection = "Output Module Spec Strings Section v28";
    var OMStringsKeyPrefix = "Output Module Spec Strings Name ";
    var hiddenPrefixRE = /_HIDDEN/;
    var OMList = new Array();
    for(var i = 0; app.preferences.havePref(OMStringsPrefSection, OMStringsKeyPrefix+i, PREFType.PREF_Type_MACHINE_INDEPENDENT_OUTPUT); i++){
        currentOMName = app.preferences.getPrefAsString(OMStringsPrefSection, OMStringsKeyPrefix+i, PREFType.PREF_Type_MACHINE_INDEPENDENT_OUTPUT);
        if(currentOMName.match(hiddenPrefixRE)==null) OMList.push(currentOMName);
    }
    return OMList;
}

// Render

function render(output_path, template) {
    /*
     * Render
    */
    try {
        var activeComp = app.project.activeItem;
        if (activeComp) {
            var renderQueueItem = app.project.renderQueue.items.add(activeComp);
            var renderQueueOutputModule = renderQueueItem.outputModule(1);
            renderQueueOutputModule.applyTemplate(template);
            renderQueueOutputModule.file = File(importPath(output_path));

            app.beginSuppressDialogs();
            app.project.renderQueue.render();
            app.endSuppressDialogs(false);
            return renderQueueItem.status==RQItemStatus.DONE?"true":"false";
        } else
            return "Error: No sequence available to render!"
    } catch (e) {
        alert(e);
        return "Error: Could not render: "+e+" Details: "+e.stack;
    }
}


function openProject(path) {
    /*
     * Opens the project from the given path, return "true" if successful,
     * "false" otherwise.
    */
    try {
        app.open(File(path));
        return "true";
    } catch (e) {
        alert(e);
        return "false";
    }
}

