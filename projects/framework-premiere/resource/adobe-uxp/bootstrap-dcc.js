/*
 ftrack Adobe Premiere framework integration bootstrap (UXP)

 Copyright (c) 2026 ftrack
*/

(function () {
    const premierepro = require("premierepro");
    const app = premierepro.app || premierepro;
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

    function getProject() {
        if (!app || !app.project) {
            return null;
        }
        return app.project;
    }

    function getEncoderManager() {
        if (premierepro.encoderManager) {
            return premierepro.encoderManager;
        }
        if (app && app.encoderManager) {
            return app.encoderManager;
        }
        return null;
    }

    async function getProjectPath() {
        try {
            const project = getProject();
            if (!project || !project.path) {
                return "";
            }
            return exportPath(String(project.path));
        } catch (error) {
            console.error(error);
            return "Error: could not get project path: " + error;
        }
    }

    async function saveProject() {
        try {
            const project = getProject();
            if (!project) {
                return "Error: could not save project: no project available";
            }

            if (typeof project.save === "function") {
                const result = await project.save();
                if (result === false) {
                    return "Error: could not save project";
                }
            } else if (typeof app.saveProject === "function") {
                const result = await app.saveProject();
                if (result === false) {
                    return "Error: could not save project";
                }
            } else {
                return "Error: could not save project: save API unavailable";
            }

            return true;
        } catch (error) {
            console.error(error);
            return "Error: could not save project: " + error;
        }
    }

    async function saveProjectAs(tempPath) {
        try {
            const targetPath = importPath(tempPath);
            const project = getProject();
            if (!project) {
                return "Error: could not save project to custom location: no project available";
            }

            if (typeof project.saveAs === "function") {
                const result = await project.saveAs(targetPath);
                if (result === false) {
                    return "Error: could not save project to custom location";
                }
            } else if (typeof app.saveProjectAs === "function") {
                const result = await app.saveProjectAs(targetPath);
                if (result === false) {
                    return "Error: could not save project to custom location";
                }
            } else {
                return "Error: could not save project to custom location: saveAs API unavailable";
            }

            return true;
        } catch (error) {
            console.error(error);
            return "Error: could not save project to custom location: " + error;
        }
    }

    async function render(outputPath, presetPath) {
        try {
            const encoderManager = getEncoderManager();
            const project = getProject();

            if (!project) {
                return "Error: Could not render: no project available";
            }

            const sequence = project.activeSequence || (typeof app.getActiveSequence === "function" ? app.getActiveSequence() : null);
            if (!sequence) {
                return "Error: No sequence available to render!";
            }

            const exportPathNormalized = importPath(outputPath);
            const presetPathNormalized = importPath(presetPath);

            if (encoderManager && typeof encoderManager.encodeSequence === "function") {
                const encodeResult = await encoderManager.encodeSequence(
                    sequence,
                    exportPathNormalized,
                    presetPathNormalized,
                );
                if (encodeResult === false) {
                    return "Error: Could not render: encoder failed";
                }
                return true;
            }

            if (typeof sequence.exportAsMediaDirect === "function") {
                let workAreaMode = undefined;
                if (app.encoder && app.encoder.ENCODE_WORKAREA !== undefined) {
                    workAreaMode = app.encoder.ENCODE_WORKAREA;
                }

                const legacyResult = await sequence.exportAsMediaDirect(
                    exportPathNormalized,
                    presetPathNormalized,
                    workAreaMode,
                );

                if (legacyResult === "No Error" || legacyResult === true) {
                    return true;
                }
                return "Error: Could not render: " + legacyResult;
            }

            return "Error: Could not render: export API unavailable";
        } catch (error) {
            console.error(error);
            return "Error: Could not render: " + error;
        }
    }

    async function openProject(path) {
        try {
            const normalizedPath = importPath(path);

            if (app && typeof app.openDocument === "function") {
                const result = await app.openDocument(normalizedPath);
                if (result === false) {
                    return false;
                }
                return true;
            }

            if (app && typeof app.openProject === "function") {
                const result = await app.openProject(normalizedPath);
                if (result === false) {
                    return false;
                }
                return true;
            }

            return false;
        } catch (error) {
            console.error(error);
            return false;
        }
    }

    window.FTRACK_RPC_FUNCTION_MAPPING = {
        getProjectPath: "getProjectPath",
        saveProject: "saveProject",
        saveProjectAs: "saveProjectAs",
        render: "render",
        openProject: "openProject",
    };

    window.FTRACK_RPC_FUNCTIONS = {
        getProjectPath: getProjectPath,
        saveProject: saveProject,
        saveProjectAs: saveProjectAs,
        render: render,
        openProject: openProject,
    };

    window.ftrackInitialiseExtension = function (session, event_manager, remote_integration_session_id) {
        // Do additional initialisations here
    };

    window.ftrackIntegrationConnected = function () {
        // React upon integration connected
    };
})();
