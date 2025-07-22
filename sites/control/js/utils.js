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

function getControllerPrice(controller) {
    const prices = {
        'arduino_uno': 25,
        'arduino_nano': 15,
        'esp32': 12,
        'esp8266': 8
    };
    return prices[controller] || 20;
}

function getStripPrice(ledsPerMeter) {
    const prices = {
        30: 15,
        60: 25,
        144: 45,
        256: 80
    };
    return prices[ledsPerMeter] || 25;
}

function getPowerSupplyPrice(powerSupply) {
    const prices = {
        '5V2A': 15,
        '5V5A': 25,
        '5V10A': 35,
        '5V20A': 55,
        '5V30A': 75,
        '5V40A': 95
    };
    return prices[powerSupply] || 35;
}

function getRecommendedPSU(maxPower) {
    if (maxPower <= 20) return '5V 5A';
    if (maxPower <= 40) return '5V 10A';
    if (maxPower <= 80) return '5V 20A';
    if (maxPower <= 120) return '5V 30A';
    return '5V 40A';
}

function getControllerName(controller) {
    const names = {
        'arduino_uno': 'Arduino Uno R3',
        'arduino_nano': 'Arduino Nano',
        'esp32': 'ESP32 Dev Board',
        'esp8266': 'ESP8266 NodeMCU'
    };
    return names[controller] || 'Arduino Uno R3';
}
