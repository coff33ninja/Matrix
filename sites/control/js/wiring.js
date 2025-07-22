// sites/control/js/wiring.js

function setupWiringEventListeners() {
    // Wiring section
    document.getElementById('generate-wiring').addEventListener('click', () => window.matrixController.generateWiring());
    document.getElementById('download-wiring').addEventListener('click', () => window.matrixController.downloadWiring());
    document.getElementById('update-calculations').addEventListener('click', () => window.matrixController.updatePowerCalculations());

    // Add event listeners for real-time updates
    ['wiring-width', 'wiring-height', 'leds-per-meter', 'power-supply', 'wiring-controller'].forEach(id => {
        const element = document.getElementById(id);
        if (element) {
            element.addEventListener('change', () => window.matrixController.updatePowerCalculations());
        }
    });
    document.getElementById('wiring-width').addEventListener('input', () => window.matrixController.updatePowerCalculations());
    document.getElementById('wiring-height').addEventListener('input', () => window.matrixController.updatePowerCalculations());
}

function initializeWiringSection() {
    window.matrixController.updatePowerInfo();
}
