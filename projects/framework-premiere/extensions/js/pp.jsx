/*
ftrack Premiere Framework integration CEP interface functions

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

/*
 * Returns the path of the document, or an empty string if it has not been saved
*/
function getProjectPath() {
    try {
        return exportPath(app.project.path);
    } catch (e) {
        alert(e);
        return "Error: could not get project path: "+e+" Details: "+e.stack;
    }
}

/*
 * Save the current project
 *
 * Note: Can't check if document is saved in premiere
*/
function saveProject() {
    try {
        app.project.save();
        return "true";
    } catch (e) {
        alert(e);
        return "Error: could not save project: "+e+" Details: "+e.stack;
    }
}

/*
 * Saves the project to the given temp_path, return "true" if successful,
 * "false" otherwise. Support psd or psb format.
*/
function saveProjectAs(temp_path) {
    try {
        app.project.saveAs(importPath(temp_path));
        return "true";
    } catch (e) {
        alert(e);
        return "Error: could not save project to custom location: "+e+" Details: "+e.stack;
    }
}

// Render

/*
 * Render the current active sequence to the given output_path using the given preset
*/
function render(output_path, preset_path) {
    try {
        app.enableQE();
        var seq = app.project.activeSequence;

        if (seq) {
            var retval = seq.exportAsMediaDirect(importPath(output_path),
                                    importPath(preset_path),
                                    app.encoder.ENCODE_WORKAREA);
            return retval=="No Error"?"true":"false";
        } else
            return "Error: No sequence available to render!"
    } catch (e) {
        alert(e);
        return "Error: Could not render: "+e+" Details: "+e.stack;
    }
}


/*
 * Opens the project from the given path, return "true" if successful,
 * "false" otherwise.
*/
function openProject(path) {
    try {
        app.openDocument(path);
        return "true";
    } catch (e) {
        alert(e);
        return "false";
    }
}

/**
 * Create bins in root based on treepath provided on the form 'ftrack/entity1/entity2...'
*/
function createBins(treepath) {
    var root = app.project.rootItem;
    var result = root;
    var folders = treepath.split("/");
    for (var i=0; i<folders.length; i++) {
        var folder = null;
        for (var j=0; j<result.children.length; j++) {
            if (result.children[j].name == folders[i]) {
                folder = result.children[j];
                break;
            }
        }
        if (!folder) {
            folder = result.createBin(folders[i]);
        }
        result = folder;
    }
    return result;
}

/*
 * Loads the file asset into the current project at the given tree path (created if not exists).
*/
function loadAsset(path, treepath, members) {
    if (hasProject() == "false") {
        alert("No project open, can't load image");
        return "false";
    }
    try {
        var root = app.project.rootItem;
        // Expect treepath to be in the form "folder1/folder2/folder3", create folders if not exists
        var parent = root;
        if (treepath && treepath !== "") {
            parent = createBins(treepath);
        }
        if (members && members.length > 0) {
            // Dealing with a image sequence, expand it
            var files = [];
            var sequence_folder = importPath(path);
            var member_list = members.split(",");
            for (var i=0; i<member_list.length; i++) {
                files.push(sequence_folder+"/"+member_list[i]);
            }
            if (app.project.importFiles(files, false, parent, true)) {
                return "true";
            } else {
                alert("Failed to import sequence files: "+path+"["+member_list+"] to "+treepath);
                return "false";
            }
        } else {
            var files = [importPath(path)];
            if (app.project.importFiles(files, false, parent, false)) {
                return "true";
            } else {
                alert("Failed to import single file: "+path+" to "+treepath);
                return "false";
            }
        }
    } catch (e) {
        alert(e);
        return "false";
    }
};
