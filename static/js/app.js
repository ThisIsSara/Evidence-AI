// app.js
// Page-specific wiring for the demo case page (templates/case_detail.html).
// All the actual pipeline animation and report rendering logic is shared
// with the custom investigation page - see static/js/investigation_ui.js.

document.addEventListener("DOMContentLoaded", () => {
    const runButton = document.getElementById("run-investigation-btn");
    const statusText = document.getElementById("pipeline-status");

    // Only the demo case page has this button, so guard against it being absent.
    if (!runButton) {
        return;
    }

    runButton.addEventListener("click", () => {
        runInvestigationFlow({
            button: runButton,
            statusText: statusText,
            requestFn: () => postJSON("/run-investigation"),
        });
    });
});
