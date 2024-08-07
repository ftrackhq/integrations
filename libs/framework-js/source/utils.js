/*
 ftrack framework Javascript utils

 Copyright (c) 2024 ftrack
*/

function sleep(ms) {
    /* Sleep for *ms* milliseconds and then continue execution. */
    return new Promise(resolve => setTimeout(resolve, ms));
}

function showElement(element_id, show) {
    /* Show or hide element with *element_id*, based on boolean *show* */
    document.getElementById(element_id).style.visibility = show?"visible":"hidden";
    document.getElementById(element_id).style.display = show?"block":"none";
}

function error(message, show_alert=true) {
    /* Show error *message*, hiding connecting element. */
    showElement("connecting", false);
    document.getElementById("error").innerHTML = message;
    showElement("error", true);
    if (show_alert) {
        alert(message);
    }
}