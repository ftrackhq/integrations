/*
 ftrack Adobe Photoshop framework integration bootstrap (UXP)

 Copyright (c) 2026 ftrack
*/

(function () {
    const { app, core } = require("photoshop");
    const { storage } = require("uxp");
    const os = require("os");

    function exportPath(path) {
        if (typeof path !== "string") {
            return path;
        }
        return path.replace(/\\/g, "/");
    }

    function importPath(path) {
        if (typeof path !== "string") {
            return path;
        }
        if (os.platform().indexOf("win") === 0) {
            return path.replace(/\//g, "\\");
        }
        return path;
    }

    function toFileUrl(path) {
        if (typeof path !== "string") {
            throw new Error("Invalid path type");
        }
        if (path.indexOf("file:") === 0) {
            return path;
        }

        const normalized = importPath(path).replace(/\\/g, "/");
        if (normalized.indexOf("/") === 0) {
            return "file:" + normalized;
        }
        return "file:/" + normalized;
    }

    async function createFileEntry(nativePath) {
        const fs = storage.localFileSystem;
        return fs.createEntryWithUrl(toFileUrl(nativePath), { overwrite: true });
    }

    async function runModal(commandName, callback) {
        return core.executeAsModal(async () => {
            return callback();
        }, {
            commandName: commandName,
        });
    }

    async function hasDocument() {
        return !!(app.documents && app.documents.length > 0);
    }

    async function documentSaved() {
        if (!(await hasDocument())) {
            return "No document open!";
        }

        return !!app.activeDocument.saved;
    }

    async function getDocumentPath() {
        try {
            if (!(await hasDocument())) {
                return "";
            }

            const fullPath = app.activeDocument.path;
            if (!fullPath) {
                return "";
            }
            return exportPath(String(fullPath));
        } catch (error) {
            return "";
        }
    }

    async function getDocumentData() {
        if (!(await hasDocument())) {
            return {};
        }

        const activeDoc = app.activeDocument;
        const fullPath = await getDocumentPath();
        const result = {
            name: String(activeDoc.name || ""),
            width: String(activeDoc.width || ""),
            height: String(activeDoc.height || ""),
            resolution: String(activeDoc.resolution || ""),
            saved: !!activeDoc.saved,
        };

        if (fullPath && fullPath.length > 0) {
            result.path = exportPath(String(activeDoc.path || ""));
            result.full_path = fullPath;
        }

        return result;
    }

    async function saveDocument(tempPath, extensionFormat) {
        try {
            if (!(await hasDocument())) {
                return false;
            }

            const normalizedPath = importPath(tempPath);

            await runModal("ftrack save document", async () => {
                const entry = await createFileEntry(normalizedPath);
                const document = app.activeDocument;

                if (extensionFormat === "psb") {
                    await document.saveAs.psb(
                        entry,
                        {
                            maximizeCompatibility: true,
                        },
                        true,
                    );
                } else {
                    await document.saveAs.psd(
                        entry,
                        {
                            maximizeCompatibility: true,
                        },
                        true,
                    );
                }
            });

            return true;
        } catch (error) {
            console.error(error);
            return "Error: Could not save document: " + error;
        }
    }

    async function exportDocument(outputPath, format) {
        if (!(await hasDocument())) {
            return false;
        }

        const normalizedFormat = String(format || "").toLowerCase();

        try {
            const normalizedPath = importPath(outputPath);

            await runModal("ftrack export document", async () => {
                const entry = await createFileEntry(normalizedPath);
                const document = app.activeDocument;

                if (normalizedFormat === "bmp") {
                    await document.saveAs.bmp(entry, {}, true);
                } else if (normalizedFormat === "gif") {
                    await document.saveAs.gif(entry, {}, true);
                } else if (normalizedFormat === "jpg") {
                    await document.saveAs.jpg(
                        entry,
                        {
                            quality: 12,
                        },
                        true,
                    );
                } else if (normalizedFormat === "png") {
                    await document.saveAs.png(entry, {}, true);
                } else {
                    throw new Error("Unknown export format: " + normalizedFormat);
                }
            });

            return true;
        } catch (error) {
            console.error(error);
            return "Error: Could not export document: " + error;
        }
    }

    async function openDocument(path) {
        try {
            const normalizedPath = importPath(path);
            await runModal("ftrack open document", async () => {
                const fs = storage.localFileSystem;
                const entry = await fs.getEntryWithUrl(toFileUrl(normalizedPath));
                await app.open(entry);
            });
            return true;
        } catch (error) {
            console.error(error);
            return false;
        }
    }

    window.FTRACK_RPC_FUNCTION_MAPPING = {
        hasDocument: "hasDocument",
        documentSaved: "documentSaved",
        getDocumentPath: "getDocumentPath",
        getDocumentData: "getDocumentData",
        saveDocument: "saveDocument",
        exportDocument: "exportDocument",
        openDocument: "openDocument",
    };

    window.FTRACK_RPC_FUNCTIONS = {
        hasDocument: hasDocument,
        documentSaved: documentSaved,
        getDocumentPath: getDocumentPath,
        getDocumentData: getDocumentData,
        saveDocument: saveDocument,
        exportDocument: exportDocument,
        openDocument: openDocument,
    };

    window.ftrackInitialiseExtension = function (session, event_manager, remote_integration_session_id) {
        // Do additional initialisations here
    };

    window.ftrackIntegrationConnected = function () {
        // React upon integration connected
    };
})();
