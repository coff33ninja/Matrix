// sites/control/js/config.js

function setupConfigEventListeners() {
    // Config section
    document.getElementById('save-config').addEventListener('click', () => window.matrixController.saveConfig());
    document.getElementById('test-connection').addEventListener('click', () => window.matrixController.testConnection());
    document.getElementById('create-backup').addEventListener('click', () => window.matrixController.createBackup());
    document.getElementById('restore-backup').addEventListener('click', () => window.matrixController.restoreBackup());
}

async function initializeConfigSection() {
    await window.matrixController.loadConfig();
}
