/**
 * Harmony ftrack integration
 * 
 * Base extensions
 */

const EXTENSION_TYPE="js_functions"
const EXTENSION_NAME="framework-harmony"


function processEvent(integration, topic, data, id) {
	info("(Extension) Processing incoming '"+topic+"' event: "+JSON.stringify(data));
    if (topic === TOPIC_RENDER_DO) {
        if (pipeline_data === undefined) {
            warning("Cannot render, no pipeline event data supplied!");
            return;
        }
        start = this.get_start_frame()
        if (pipeline_data.start_frame != undefined)
            start_frame = pipeline_data.start_frame;
        end = this.get_end_frame()
        if (pipeline_data.end_frame != undefined)
            end_frame = pipeline_data.end_frame;
        destination_path = pipeline_data.destination_path;
        prefix = pipeline_data.prefix;
        extension = pipeline_data.extension;
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
        integration.send(TOPIC_RENDER_FINISHED, {}, id)
    }
}

function testFunc(arg) {
	MessageBox.information("testing: "+arg);
}