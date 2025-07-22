// sites/control/js/generator.js

function setupGeneratorEventListeners() {
    // Generator section
    document.getElementById('generate-code').addEventListener('click', () => window.matrixController.generateArduinoCode());
    document.getElementById('download-code').addEventListener('click', () => window.matrixController.downloadCode());
    document.getElementById('matrix-width').addEventListener('input', () => window.matrixController.updateBoardComparison());
    document.getElementById('matrix-height').addEventListener('input', () => window.matrixController.updateBoardComparison());
}

function initializeGeneratorSection() {
    window.matrixController.updateBoardComparison();
}
