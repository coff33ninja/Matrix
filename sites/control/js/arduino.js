// sites/control/js/arduino.js

function setupArduinoEventListeners() {
    document.getElementById('arduino-brightness').addEventListener('input', (e) => {
        document.getElementById('arduino-brightness-display').textContent = e.target.value;
    });

    document.getElementById('arduino-board').addEventListener('change', () => {
        window.matrixController.syncArduinoSettings();
    });

    document.getElementById('generate-arduino').addEventListener('click', () => window.matrixController.generateArduinoPackage());
    document.getElementById('preview-code').addEventListener('click', () => window.matrixController.previewArduinoCode());
    document.getElementById('download-package').addEventListener('click', () => window.matrixController.downloadArduinoPackage());
    document.getElementById('copy-code').addEventListener('click', () => window.matrixController.copyArduinoCode());
    document.getElementById('download-ino').addEventListener('click', () => window.matrixController.downloadArduinoFile());
}

function initializeArduinoSection() {
    window.matrixController.syncArduinoSettings();
}
