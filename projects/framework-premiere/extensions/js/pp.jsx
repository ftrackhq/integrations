/*
ftrack Photoshop Framework integration CEP interface functions

Exposed by RPC call event to Python standalone host.

Copyright (c) 2024 ftrack
*/

//#target premiere

function render(output_path, preset_path) {
    /*
     * Render
    */
    try {
        app.enableQE();
        var seq = app.project.activeSequence;

        if (seq) {
            seq.exportAsMediaDirect(output_path,
                                    preset_path,
                                    app.encoder.ENCODE_WORKAREA);
            return "true";
        } else
            return "No sequence available to render!"
    } catch (e) {
        return "An error occurred: "+e+" Details: "+e.stack;
    }
}
