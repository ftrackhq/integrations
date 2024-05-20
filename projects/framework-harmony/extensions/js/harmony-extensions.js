/**
 * Harmony ftrack integration
 * 
 * Base extensions
 */
"use strict";

const EXTENSION_TYPE="js_functions"
const EXTENSION_NAME="framework-harmony"


function processEvent(integration, topic, data, id) {
	info("(Extensions) Processing incoming '"+topic+"' event: "+JSON.stringify(data));
}

function renderSequence(destination_path, prefix, extension) {
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
    info("(Extensions) Rendering '"+integration.getScenePath()+"', frames: "+start+"-"+end+" > "+destination_path)

    function frameReady(frame, celImage)
    {
        var imagePath = destination_path + "/" + prefix + "." + frame + "." + extension;
        // Save the image here.
        celImage.imageFile(imagePath);

        info("Frame " + frame + " ready @ "+imagePath);
    }
    function renderFinished()
    {
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