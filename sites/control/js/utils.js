// sites/control/js/utils.js

function hexToRgb(hex) {
    const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
    return result ? {
        r: parseInt(result[1], 16),
        g: parseInt(result[2], 16),
        b: parseInt(result[3], 16)
    } : { r: 0, g: 0, b: 0 };
}

function log(message, type = 'info') {
    const logContainer = document.getElementById('activity-log');
    if (!logContainer) return;
    const timestamp = new Date().toLocaleTimeString();
    const entry = document.createElement('div');
    entry.className = `log-entry ${type}`;
    entry.textContent = `[${timestamp}] ${message}`;

    logContainer.appendChild(entry);
    logContainer.scrollTop = logContainer.scrollHeight;

    // Keep only last 100 entries
    while (logContainer.children.length > 100) {
        logContainer.removeChild(logContainer.firstChild);
    }
}

// ⚠️ DEPRECATED: These functions contained backend logic and have been removed
// All pricing, PSU recommendations, and controller specifications are now handled by backend APIs
// Use the /api/wiring endpoint to get accurate pricing and component data

function getControllerPrice(controller) {
    console.warn('getControllerPrice() is deprecated - use backend API /api/wiring for pricing data');
    return 0; // Return 0 to indicate this should not be used
}

function getStripPrice(ledsPerMeter) {
    console.warn('getStripPrice() is deprecated - use backend API /api/wiring for pricing data');
    return 0; // Return 0 to indicate this should not be used
}

function getPowerSupplyPrice(powerSupply) {
    console.warn('getPowerSupplyPrice() is deprecated - use backend API /api/wiring for pricing data');
    return 0; // Return 0 to indicate this should not be used
}

function getRecommendedPSU(maxPower) {
    console.warn('getRecommendedPSU() is deprecated - use backend API /api/wiring for PSU recommendations');
    return 'Use Backend API'; // Return message to indicate this should not be used
}

function getControllerName(controller) {
    // This is just display mapping, can stay in frontend as it's not business logic
    const names = {
        'arduino_uno': 'Arduino Uno R3',
        'arduino_nano': 'Arduino Nano',
        'esp32': 'ESP32 Dev Board',
        'esp8266': 'ESP8266 NodeMCU'
    };
    return names[controller] || 'Arduino Uno R3';
}
