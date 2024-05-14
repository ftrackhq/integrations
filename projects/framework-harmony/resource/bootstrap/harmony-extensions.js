/**
 * Harmony ftrack integration
 * 
 * Base extensions
 */
"use strict";

const EXTENSION_TYPE="js_functions"
const EXTENSION_NAME="framework-harmony"


function processEvent(integration, topic, data, id) {
	info("(Extension) Processing incoming '"+topic+"' event: "+JSON.stringify(data));
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
    end = this.getEndFrame()
    //if (data.end_frame != undefined)
    //    end_frame = data.end_frame;
    info("(render) Rendering '"+this.get_scene_path()+"', frames: "+start+"-"+end+" > "+destination_path)

    function frameReady(frame, celImage)
    {
        info("(render) Frame " + frame + " Ready.");
        // Save the image here.
        celImage.imageFile(destination_path + prefix + "." + frame + extension);
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

    info("(render)  Render finished");

    // Send reply back
    integration.send(topic, {}, id)
}