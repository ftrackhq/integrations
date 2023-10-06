/*
ftrack Photoshop Framework integration CEP interface

Copyright (c) 2014-2023 ftrack
*/

#target photoshop

function debugPS() {
    return app.activeDocument;
}

function getDocumentPath() {
    try {
        var f = new File(app.activeDocument.fullName);
        var result = f.fsName;
        f.close();
        return result;
    } catch (e) {
        return "";
    }
}

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

function saveDocument(temp_path) {
    try {
        if (documents.length == 0) {
            // No document open
            return "false";
        }
        // Has been saved?
        var full_path = getDocumentPath();
        if (full_path === "") {
            app.activeDocument.saveAs(new File(temp_path));
        } else
           app.activeDocument.save();
        return "true";
    } catch (e) {
        alert(e);
        return "false";
    }
}

function exportDocument(output_path, format) {
    if (documents.length == 0) {
        return "false";
    }
    var options;
    if (format == 'jpg') {
        options = new JPEGSaveOptions();
        options.quality = 12;
        options.embedColorProfile = true;
        options.formatOptions = FormatOptions.PROGRESSIVE;
        if (options.formatOptions == FormatOptions.PROGRESSIVE) {
            options.scans = 5;
        }
        options.matte = MatteType.NONE;
    }
    if (format == 'png') {
        options = new PNGSaveOptions();
        options.interlaced = true;
        options.transparency = true;
    }
    try {
        app.activeDocument.saveAs(new File(output_path), options, true);
        return "true";
    } catch (e) {
        alert(e);
        return "false";
    }
}
