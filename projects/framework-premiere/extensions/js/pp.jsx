/*
ftrack Premere Framework integration CEP interface functions

Exposed by RPC call event to Python standalone host.

Copyright (c) 2024 ftrack
*/


function hasProject() {
    return app.project?"true":"false";
}

// Can't check if document is saved in premiere

function getProjectPath() {
    /*
     * Returns the path of the document, or an empty string if it has not been saved
    */
    try {
        return app.project.path.replace(/\\/g, "/"); // Convert to forward slashes to fix issues with JSON encoding
    } catch (e) {
        alert(e);
        return "Error: could not get project path: "+e+" Details: "+e.stack;
    }
}

function saveProject() {
    /*
     * Save the current project
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
        app.project.saveAs(temp_path);
        return "true";
    } catch (e) {
        alert(e);
        return "Error: could not save project to custom location: "+e+" Details: "+e.stack;
    }
}

function render(output_path, preset_path) {
    /*
     * Render
    */
    try {
        app.enableQE();
        var seq = app.project.activeSequence;

        if (seq) {
            seq.exportAsMediaDirect(output_path,
                                    preset_path,
                                    app.encoder.ENCODE_WORKAREA);
            return "true";
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
        app.openDocument(path);
        return "true";
    } catch (e) {
        alert(e);
        return "false";
    }
}

