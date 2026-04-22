/*
 ftrack Adobe After Effects framework integration bootstrap (UXP)

 Copyright (c) 2026 ftrack
*/

(function () {
    const aftereffects = require("aftereffects");
    const app = aftereffects.app || aftereffects;
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

    async function getProjectPath() {
        try {
            const project = getProject();
            if (!project || !project.file) {
                return "";
            }
            const filePath = project.file.fsName || project.file;
            return exportPath(String(filePath));
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
                await project.save();
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
                await project.saveAs(targetPath);
            } else if (typeof project.save === "function") {
                // Fallback: AE ExtendScript-style save with File argument
                await project.save(targetPath);
            } else {
                return "Error: could not save project to custom location: saveAs API unavailable";
            }

            return true;
        } catch (error) {
            console.error(error);
            return "Error: could not save project to custom location: " + error;
        }
    }

    async function getOutputModuleTemplateNames() {
        try {
            const project = getProject();
            if (!project) {
                return [];
            }

            // UXP API: query output module templates from preferences
            // AE stores templates in preferences under a specific section
            if (app.preferences && typeof app.preferences.getPrefAsString === "function") {
                var OMStringsPrefSection = "Output Module Spec Strings Section v28";
                var OMStringsKeyPrefix = "Output Module Spec Strings Name ";
                var hiddenPrefixRE = /_HIDDEN/;
                var OMList = [];
                var prefType = undefined;

                // Resolve preference type constant
                if (typeof PREFType !== "undefined" && PREFType.PREF_Type_MACHINE_INDEPENDENT_OUTPUT !== undefined) {
                    prefType = PREFType.PREF_Type_MACHINE_INDEPENDENT_OUTPUT;
                }

                for (var i = 0; ; i++) {
                    var hasPref = false;
                    try {
                        if (prefType !== undefined) {
                            hasPref = app.preferences.havePref(OMStringsPrefSection, OMStringsKeyPrefix + i, prefType);
                        } else {
                            hasPref = app.preferences.havePref(OMStringsPrefSection, OMStringsKeyPrefix + i);
                        }
                    } catch (e) {
                        break;
                    }

                    if (!hasPref) {
                        break;
                    }

                    var currentOMName;
                    try {
                        if (prefType !== undefined) {
                            currentOMName = app.preferences.getPrefAsString(OMStringsPrefSection, OMStringsKeyPrefix + i, prefType);
                        } else {
                            currentOMName = app.preferences.getPrefAsString(OMStringsPrefSection, OMStringsKeyPrefix + i);
                        }
                    } catch (e) {
                        break;
                    }

                    if (currentOMName && !currentOMName.match(hiddenPrefixRE)) {
                        OMList.push(currentOMName);
                    }
                }

                return OMList;
            }

            return [];
        } catch (error) {
            console.error(error);
            return "Error: could not get output module templates: " + error;
        }
    }

    async function render(outputPath, template) {
        try {
            const project = getProject();
            if (!project) {
                return "Error: Could not render: no project available";
            }

            const activeComp = project.activeItem;
            if (!activeComp) {
                return "Error: No composition available to render!";
            }

            const exportPathNormalized = importPath(outputPath);

            // Add composition to render queue
            var renderQueueItem = project.renderQueue.items.add(activeComp);
            var renderQueueOutputModule = renderQueueItem.outputModule(1);

            // Apply output module template
            if (template && typeof renderQueueOutputModule.applyTemplate === "function") {
                renderQueueOutputModule.applyTemplate(template);
            }

            // Set output file path
            renderQueueOutputModule.file = exportPathNormalized;

            // Suppress dialogs and render
            if (typeof app.beginSuppressDialogs === "function") {
                app.beginSuppressDialogs();
            }

            await project.renderQueue.render();

            if (typeof app.endSuppressDialogs === "function") {
                app.endSuppressDialogs(false);
            }

            // Check render status
            // RQItemStatus.DONE == 3013 in ExtendScript
            var status = renderQueueItem.status;
            if (status === 3013 || String(status) === "DONE" || status === "done") {
                return true;
            }

            return "Error: Render did not complete successfully, status: " + String(status);
        } catch (error) {
            console.error(error);
            return "Error: Could not render: " + error;
        }
    }

    async function openProject(path) {
        try {
            const normalizedPath = importPath(path);

            if (typeof app.open === "function") {
                await app.open(normalizedPath);
                return true;
            }

            if (typeof app.openFile === "function") {
                await app.openFile(normalizedPath);
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
        getOutputModuleTemplateNames: "getOutputModuleTemplateNames",
        render: "render",
        openProject: "openProject",
    };

    window.FTRACK_RPC_FUNCTIONS = {
        getProjectPath: getProjectPath,
        saveProject: saveProject,
        saveProjectAs: saveProjectAs,
        getOutputModuleTemplateNames: getOutputModuleTemplateNames,
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
