/**
 * Harmony ftrack integration
 * 
 * Harmony commands
 *
 * Copyright (c) 2024 ftrack
 */
"use strict";

// RPC functions

/**
* Render current project to an image sequence
*
* @param {string} destination_path The folder to render to
* @param {string} prefix The prefix for the image files
* @param {string} extension
* @param {string} format_option
* @returns {boolean} True if successful
*/
function renderSequence(destination_path, prefix, extension, format_option) {
    if (destination_path === undefined) {
        warning("Cannot render, no destination path given!");
        return false;
    }
    var integration = getIntegration();
    if (prefix === undefined) {
        prefix = "image";
    }
    if (extension === undefined) {
        extension = "png";
    }
    start = integration.getStartFrame()
    //if (data.start_frame != undefined)
    //    start_frame = data.start_frame;
    end = integration.getEndFrame()
    //if (data.end_frame != undefined)
    //    end_frame = data.end_frame;
    info("(Extensions) Rendering '"+integration.getScenePath()+"', frames: "+start+"-"+end+" > "+destination_path+" using format/extension: "+extension+" with option: "+format_option);

    function frameReady(frame, celImage) {
        var imagePath = destination_path + "/" + prefix + "." + frame + "." + extension;
        // Save the image here.
        if (format_option !== undefined && format_option.length > 0) {
            celImage.imageFile(imagePath, extension, format_option);
        } else
            celImage.imageFile(imagePath, extension);
        info("Frame " + frame + " ready @ "+imagePath);
    }
    function renderFinished() {
        info("Render Finished");
    }
    render.renderFinished.connect(renderFinished);
    render.frameReady.connect(frameReady);
    render.setRenderDisplay("Top/Display");
    render.renderSceneAll();
    render.renderFinished.disconnect(renderFinished);
    render.frameReady.disconnect(frameReady);

    info("Render finished");

    return true;
}

/**
* Return the current scene folder path.
*
* @returns {string} The current project path
*/
function getScenePath() {
    return scene.currentProjectPath();
}

/**
* Save the current scene (all modified files) to disk.
*
* @returns {boolean} True if the save succeeded
*/
function saveScene() {
    info("Saving Harmony scene");
    return scene.saveAll();
}

/**
* Close the current scene and open the offline scene at *file_path*.
*
* @param {string} file_path Path to the .xstage file of the scene to open
* @returns {boolean} True if the scene was opened
*/
function openScene(file_path) {
    if (file_path === undefined || file_path.length === 0) {
        warning("Cannot open scene, no file path given!");
        return false;
    }
    info("Opening Harmony scene (offline): " + file_path);
    return scene.closeSceneAndOpenOffline(file_path);
}

info("(Harmony Commands) Loaded");