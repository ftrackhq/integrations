/*
ftrack Photoshop Framework integration extendscript base functions

Exposed by RPC call event to Python standalone host.

Copyright (c) 2024 ftrack
*/

#target photoshop

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

// Document


/*
* Returns 'true' if there is a document open, 'false' otherwise
*/
function hasDocument() {
    return documents.length > 0?"true":"false";
}

/*
* Returns the name of the active document, or an empty string if there is no document open.
*/
function documentSaved() {
     if (documents.length == 0) {
        return "No document open!";
    }
    const activeDoc = app.activeDocument;
    return activeDoc.saved?"true":"false";
}

/*
* Returns the path of the document, or an empty string if it has not been saved
*/
function getDocumentPath() {
    try {
        var f = new File(app.activeDocument.fullName);
        var result = f.fsName;
        f.close();
        return exportPath(result);
    } catch (e) {
        return "";
    }
}

/*
* Returns a JSON string with the document data, or an empty JSON string if
* there is no document open.
*/
function getDocumentData() {
     if (documents.length == 0) {
        // No document open
        return '{}';
    }

    var full_path = getDocumentPath();

    const activeDoc = app.activeDocument;

    result = '{'+
        '"name": "'+activeDoc.name+'",'+
        '"width":"'+activeDoc.width+'",'+
        '"height":"'+activeDoc.height+'",'+
        '"resolution":"'+activeDoc.resolution+'"';

    if (full_path.length > 0) {
        // It has been saved somewhere
        result += ',"path":"'+activeDoc.path+'",'+
            '"full_path":"'+full_path+'"';

    }
    result += ',"saved":'+(activeDoc.saved?'true':'false');

    return result + '}';

}

/*
* Saves the document to the given temp_path, return "true" if successful,
* error message otherwise. Support psd or psb format.
*/
function saveDocument(temp_path, extension_format) {

    try {
        if (documents.length == 0) {
            // No document open
            return "false";
        }

        if (extension_format == 'psb') {
            var desc1 = new ActionDescriptor();
            var desc2 = new ActionDescriptor();
            desc2.putBoolean( stringIDToTypeID('maximizeCompatibility'), true );
            desc1.putObject( charIDToTypeID('As  '), charIDToTypeID('Pht8'), desc2 );
            desc1.putPath( charIDToTypeID('In  '), new File(temp_path) );
            desc1.putBoolean( charIDToTypeID('LwCs'), true );
            executeAction( charIDToTypeID('save'), desc1, DialogModes.NO );
        } else {
            app.activeDocument.saveAs(new File(temp_path));
        }
        return "true";
    } catch (e) {
        alert(e);
        return "false";
    }
}

/*
 * Exports the document to the given output_path, return "true" if successful,
 * error message otherwise.
*/
function exportDocument(output_path, format) {
    if (documents.length == 0) {
        // No document open
        return "false";
    }
    try {
        var options;
        if (format == 'bmp') {
            options = new BMPSaveOptions();
            options.alphaChannels = true;
            options.rleCompression = true;
        } else if (format == 'eps') {
            options = new EPSSaveOptions();
        } else if (format == 'gif') {
            options = new GIFSaveOptions();
        } else if (format == 'gif') {
            options = new GIFSaveOptions();
        } else if (format == 'jpg') {
            options = new JPEGSaveOptions();
            options.quality = 12;
            options.embedColorProfile = true;
            options.formatOptions = FormatOptions.PROGRESSIVE;
            if (options.formatOptions == FormatOptions.PROGRESSIVE) {
                options.scans = 5;
            }
            options.matte = MatteType.NONE;
        } else if (format == 'pdf') {
            options = new PDFSaveOptions();
            options.alphaChannels = true;
            options.annotations = true;
            options.embedColorProfile = true;
        } else if (format == 'png') {
            options = new PNGSaveOptions();
            options.interlaced = true;
            options.transparency = true;
        } else if (format == 'tif') {
            options = new TiffSaveOptions();
            options.alphaChannels = true;
            options.annotations = false
            options:transparency = true;
        } else {
            return "Unknown export format: "+format
        }
        app.activeDocument.saveAs(new File(importPath(output_path)), options, true);
        return "true";
    } catch (e) {
        alert(e);
        return "Error: Could not export document: "+e+" Details: "+e.stack;
    }
}

/*
* Opens the document from the given path, return "true" if successful,
* "false" otherwise.
*/
function openDocument(path) {
    try {
        var file = new File(importPath(path));
        app.open(file);
        return "true";
    } catch (e) {
        alert(e);
        return "false";
    }
}

/*
* Load image in photoshop
*/
function loadImage(path) {
    try {
        var file = new File(importPath(path));
        var openedDoc = app.open(file); // Load the image file
        return "true";
    } catch (e) {
        alert(e);
        return "false";
    }
}