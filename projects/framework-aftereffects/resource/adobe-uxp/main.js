const { entrypoints } = require("uxp");


entrypoints.setup({
    plugin: {
        create() {
            console.log("ftrack After Effects UXP plugin created");
        },
        destroy() {
            console.log("ftrack After Effects UXP plugin destroyed");
        },
    },
    panels: {
        ftrackPanel: {
            show() {
                // Panel UI and bootstrap are loaded through index.html.
            },
        },
    },
});
