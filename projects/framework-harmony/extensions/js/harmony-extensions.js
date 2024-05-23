/**
 * Harmony ftrack integration
 * 
 * Base extensions
 */
"use strict";

const EXTENSION_TYPE="js_functions"
const EXTENSION_NAME="framework-harmony"

// RPC functions

/**
* Render current project to an image sequence
*
* @param {string} destination_path
* @param {string} prefix
* @param {string} extension
*/
function renderSequence(destination_path, prefix, extension, format_option) {
    if (destination_path === undefined) {
        warning("Cannot render, no destination path given!");
        return;
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

info("(Extensions) Loaded");