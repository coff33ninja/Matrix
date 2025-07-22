// sites/control/js/control.js
// This file is now integrated into app.js for better organization

// Legacy functions for backward compatibility
function setupControlEventListeners() {
    // This is now handled by MatrixController.setupControlEventListeners()
    if (window.matrixController) {
        window.matrixController.setupControlEventListeners();
    }
}

function initializeControlSection() {
    // This is now handled by MatrixController.initializeControlSection()
    if (window.matrixController) {
        window.matrixController.initializeControlSection();
    }
}

function setupDrawingEventListeners() {
    // This is now handled by MatrixController.setupDrawingEventListeners()
    if (window.matrixController) {
        window.matrixController.setupDrawingEventListeners();
    }
}