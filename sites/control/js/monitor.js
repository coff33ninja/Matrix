// sites/control/js/monitor.js

function setupMonitorEventListeners() {
    // No event listeners specific to the monitor section itself
}

async function initializeMonitorSection() {
    await window.matrixController.loadSystemStats();
    await window.matrixController.loadHardwareInfo();
}
