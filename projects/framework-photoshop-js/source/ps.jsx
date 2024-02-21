/*
ftrack Photoshop Framework integration CEP interface functions

Exposed by RPC call event to Python standalone host.

Copyright (c) 2024 ftrack
*/

#target photoshop

function hasDocument() {
    return documents.length > 0?"true":"false";
}

function documentSaved() {
     if (documents.length == 0) {
        return "No document open!";
    }
    const activeDoc = app.activeDocument;
    return activeDoc.saved?"true":"false";
}

function getDocumentPath() {
    /*
     * Returns the path of the document, or an empty string if it has not been saved
    */
    try {
        var f = new File(app.activeDocument.fullName);
        var result = f.fsName;
        f.close();
        return result.replace(/\\/g, "/"); // Convert to forward slashes to fix issues with JSON encoding
    } catch (e) {
        return "";
    }
}

function getDocumentData() {
    /*
     * Returns a JSON string with the document data, or an empty string if there is no document open.
    */
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

function saveDocument(temp_path) {
    /*
     * Saves the document to the given temp_path, return "true" if successful,
     * "false" otherwise.
    */
    try {
        if (documents.length == 0) {
            // No document open
            return "false";
        }
        app.activeDocument.saveAs(new File(temp_path));
        return "true";
    } catch (e) {
        alert(e);
        return "false";
    }
}

function exportDocument(output_path, format) {
    /*
     * Exports the document to the given output_path, return "true" if successful,
     * "false" otherwise.
    */
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
        app.activeDocument.saveAs(new File(output_path), options, true);
        return "true";
    } catch (e) {
        return "An error occurred: "+e+" Details: "+e.stack;
    }
}

function openDocument(path) {
    /*
     * Opens the document from the given path, return "true" if successful,
     * "false" otherwise.
    */
    try {
        app.open(new File(path));
        return "true";
    } catch (e) {
        alert(e);
        return "false";
    }
}
