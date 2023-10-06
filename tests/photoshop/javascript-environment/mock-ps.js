
global.fetch = require('node-fetch');
const ftrack = require("@ftrack/api");

console.log(ftrack);

error = console.error;

class CSInterface {

    getHostEnvironment() {
        return {
            appVersion: "1.0"
        }
    }

    evalScript(
        scriptString,
        callback
    ) {
        console.log('Resolving', scriptString);
        if (scriptString.startsWith('$.getenv("')) {
            var envVariableName = scriptString.replace('$.getenv("', '').replace('")', '');
            callback(process.env[envVariableName] || "null");
            return
        }

        throw Error("Unknown scriptString to eval: " + scriptString);
    }

}

// console.log(process.env)
