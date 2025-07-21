// LED Matrix Control Center - Main Application
class MatrixController {
    constructor() {
        this.apiBase = 'http://localhost:8080';
        this.connected = false;
        this.matrixSize = { width: 16, height: 16 };
        this.currentPattern = 'solid';
        this.fps = 0;
        
        this.init();
    }

    async init() {
        this.setupEventListeners();
        this.initializeMatrix();
        await this.checkConnection();
        this.startStatusUpdates();
        this.log('System initialized', 'success');
    }

    setupEventListeners() {
        // Navigation tabs
        document.querySelectorAll('.nav-tab').forEach(tab => {
            tab.addEventListener('click', (e) => {
                e.preventDefault();
                this.switchSection(tab.dataset.section);
            });
        });

        // Control section
        document.getElementById('apply-pattern').addEventListener('click', () => this.applyPattern());
        document.getElementById('clear-matrix').addEventListener('click', () => this.clearMatrix());
        document.getElementById('test-pattern').addEventListener('click', () => this.testPattern());
        
        // Sliders
        document.getElementById('brightness-slider').addEventListener('input', (e) => {
            document.getElementById('brightness-value').textContent = e.target.value;
        });
        
        document.getElementById('speed-slider').addEventListener('input', (e) => {
            document.getElementById('speed-value').textContent = e.target.value;
        });

        // Generator section
        document.getElementById('generate-code').addEventListener('click', () => this.generateArduinoCode());
        document.getElementById('download-code').addEventListener('click', () => this.downloadCode());
        document.getElementById('matrix-width').addEventListener('input', () => this.updateBoardComparison());
        document.getElementById('matrix-height').addEventListener('input', () => this.updateBoardComparison());

        // Wiring section
        document.getElementById('generate-wiring').addEventListener('click', () => this.generateWiring());
        document.getElementById('download-wiring').addEventListener('click', () => this.downloadWiring());
        document.getElementById('wiring-width').addEventListener('input', () => this.updatePowerInfo());
        document.getElementById('wiring-height').addEventListener('input', () => this.updatePowerInfo());

        // Config section
        document.getElementById('save-config').addEventListener('click', () => this.saveConfig());
        document.getElementById('test-connection').addEventListener('click', () => this.testConnection());
        document.getElementById('create-backup').addEventListener('click', () => this.createBackup());
        document.getElementById('restore-backup').addEventListener('click', () => this.restoreBackup());
    }

    switchSection(sectionName) {
        // Update active tab
        document.querySelectorAll('.nav-tab').forEach(tab => tab.classList.remove('active'));
        document.querySelector(`[data-section="${sectionName}"]`).classList.add('active');

        // Show/hide sections
        document.querySelectorAll('.section').forEach(section => {
            section.style.display = 'none';
        });
        document.getElementById(`${sectionName}-section`).style.display = 'block';

        // Load section-specific data
        this.loadSectionData(sectionName);
    }

    async loadSectionData(section) {
        switch(section) {
            case 'monitor':
                await this.loadSystemStats();
                await this.loadHardwareInfo();
                break;
            case 'generator':
                this.updateBoardComparison();
                break;
            case 'wiring':
                this.updatePowerInfo();
                break;
            case 'config':
                await this.loadConfig();
                break;
        }
    }

    initializeMatrix() {
        const grid = document.getElementById('matrix-grid');
        const { width, height } = this.matrixSize;
        
        grid.style.gridTemplateColumns = `repeat(${width}, 1fr)`;
        grid.innerHTML = '';
        
        for (let i = 0; i < width * height; i++) {
            const pixel = document.createElement('div');
            pixel.className = 'led-pixel';
            pixel.dataset.index = i;
            grid.appendChild(pixel);
        }
        
        document.getElementById('matrix-size').textContent = `${width}×${height}`;
        document.getElementById('led-count').textContent = width * height;
    }

    async checkConnection() {
        try {
            const response = await fetch(`${this.apiBase}/status`);
            if (response.ok) {
                const data = await response.json();
                this.connected = true;
                this.updateConnectionStatus(true);
                this.log('Connected to matrix controller', 'success');
                
                // Update matrix size from server
                if (data.matrix) {
                    this.matrixSize = { width: data.matrix.width, height: data.matrix.height };
                    this.initializeMatrix();
                }
            } else {
                throw new Error('Server responded with error');
            }
        } catch (error) {
            this.connected = false;
            this.updateConnectionStatus(false);
            this.log('Failed to connect to matrix controller', 'error');
        }
    }

    updateConnectionStatus(connected) {
        const statusDot = document.getElementById('connection-status');
        const statusText = document.getElementById('connection-text');
        
        if (connected) {
            statusDot.classList.add('connected');
            statusText.textContent = 'Connected';
        } else {
            statusDot.classList.remove('connected');
            statusText.textContent = 'Disconnected';
        }
    }

    startStatusUpdates() {
        setInterval(async () => {
            await this.checkConnection();
            this.updateFPS();
        }, 2000);
    }

    updateFPS() {
        // Simulate FPS counter - in real implementation, this would come from the server
        this.fps = this.connected ? Math.floor(Math.random() * 30) + 30 : 0;
        document.getElementById('fps-counter').textContent = this.fps;
    }

    async applyPattern() {
        const pattern = document.getElementById('pattern-select').value;
        const color = document.getElementById('color-picker').value;
        const brightness = document.getElementById('brightness-slider').value;
        const speed = document.getElementById('speed-slider').value;

        try {
            const response = await fetch(`${this.apiBase}/pattern`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ pattern, color, brightness, speed })
            });

            if (response.ok) {
                this.log(`Applied pattern: ${pattern}`, 'success');
                this.updateMatrixPreview(pattern, color);
            } else {
                throw new Error('Failed to apply pattern');
            }
        } catch (error) {
            this.log(`Error applying pattern: ${error.message}`, 'error');
        }
    }

    updateMatrixPreview(pattern, color) {
        const pixels = document.querySelectorAll('.led-pixel');
        
        switch(pattern) {
            case 'solid':
                pixels.forEach(pixel => pixel.style.backgroundColor = color);
                break;
            case 'rainbow':
                pixels.forEach((pixel, index) => {
                    const hue = (index * 360) / pixels.length;
                    pixel.style.backgroundColor = `hsl(${hue}, 100%, 50%)`;
                });
                break;
            case 'plasma':
                this.animatePlasma(pixels);
                break;
            default:
                pixels.forEach(pixel => pixel.style.backgroundColor = '#333');
        }
    }

    animatePlasma(pixels) {
        let time = 0;
        const animate = () => {
            pixels.forEach((pixel, index) => {
                const x = index % this.matrixSize.width;
                const y = Math.floor(index / this.matrixSize.width);
                const hue = (Math.sin(x * 0.1 + time) + Math.sin(y * 0.1 + time)) * 180;
                pixel.style.backgroundColor = `hsl(${hue}, 100%, 50%)`;
            });
            time += 0.1;
            if (time < 10) requestAnimationFrame(animate);
        };
        animate();
    }

    async clearMatrix() {
        try {
            const response = await fetch(`${this.apiBase}/clear`, { method: 'POST' });
            if (response.ok) {
                document.querySelectorAll('.led-pixel').forEach(pixel => {
                    pixel.style.backgroundColor = '#333';
                });
                this.log('Matrix cleared', 'success');
            }
        } catch (error) {
            this.log(`Error clearing matrix: ${error.message}`, 'error');
        }
    }

    testPattern() {
        this.log('Running test pattern', 'success');
        const pixels = document.querySelectorAll('.led-pixel');
        let index = 0;
        
        const testSequence = () => {
            if (index < pixels.length) {
                pixels[index].style.backgroundColor = '#e94560';
                setTimeout(() => {
                    pixels[index].style.backgroundColor = '#333';
                    index++;
                    testSequence();
                }, 50);
            } else {
                this.log('Test pattern completed', 'success');
            }
        };
        
        testSequence();
    }

    async generateArduinoCode() {
        const board = document.getElementById('board-select').value;
        const width = document.getElementById('matrix-width').value;
        const height = document.getElementById('matrix-height').value;

        try {
            const response = await fetch(`${this.apiBase}/generate`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ board, width: parseInt(width), height: parseInt(height) })
            });

            if (response.ok) {
                const data = await response.json();
                this.log(`Arduino code generated for ${board}`, 'success');
                this.generatedCode = data.code;
            } else {
                throw new Error('Failed to generate code');
            }
        } catch (error) {
            this.log(`Error generating code: ${error.message}`, 'error');
        }
    }

    downloadCode() {
        if (this.generatedCode) {
            const blob = new Blob([this.generatedCode], { type: 'text/plain' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'led_matrix.ino';
            a.click();
            URL.revokeObjectURL(url);
            this.log('Arduino code downloaded', 'success');
        } else {
            this.log('No code to download. Generate code first.', 'warning');
        }
    }

    updateBoardComparison() {
        const width = parseInt(document.getElementById('matrix-width').value);
        const height = parseInt(document.getElementById('matrix-height').value);
        const totalLeds = width * height;
        
        const boards = {
            'uno': { name: 'Arduino Uno', memory: 2048, maxLeds: 500, voltage: '5V' },
            'nano': { name: 'Arduino Nano', memory: 2048, maxLeds: 500, voltage: '5V' },
            'esp32': { name: 'ESP32 Dev Board', memory: 520000, maxLeds: 2000, voltage: '3.3V' },
            'esp8266': { name: 'ESP8266 NodeMCU', memory: 80000, maxLeds: 800, voltage: '3.3V' },
            'mega': { name: 'Arduino Mega 2560', memory: 8192, maxLeds: 1000, voltage: '5V' }
        };

        let html = '<h4>Board Recommendations:</h4><div class="grid grid-2" style="gap: 10px; margin-top: 10px;">';
        
        Object.entries(boards).forEach(([key, board]) => {
            const suitable = totalLeds <= board.maxLeds;
            const memoryUsage = (totalLeds * 3 / board.memory * 100).toFixed(1);
            
            html += `
                <div class="card" style="padding: 10px; ${suitable ? 'border-color: var(--success)' : 'border-color: var(--error)'}">
                    <strong>${board.name}</strong><br>
                    <small>Memory: ${memoryUsage}% | ${suitable ? '✅ Suitable' : '❌ Too many LEDs'}</small>
                </div>
            `;
        });
        
        html += '</div>';
        document.getElementById('board-comparison').innerHTML = html;
    }

    async generateWiring() {
        const controller = document.getElementById('wiring-controller').value;
        const width = document.getElementById('wiring-width').value;
        const height = document.getElementById('wiring-height').value;

        try {
            const response = await fetch(`${this.apiBase}/wiring`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ controller, width: parseInt(width), height: parseInt(height) })
            });

            if (response.ok) {
                const data = await response.json();
                this.log(`Wiring guide generated for ${controller}`, 'success');
                this.wiringGuide = data.guide;
            } else {
                throw new Error('Failed to generate wiring guide');
            }
        } catch (error) {
            this.log(`Error generating wiring: ${error.message}`, 'error');
        }
    }

    downloadWiring() {
        if (this.wiringGuide) {
            const blob = new Blob([this.wiringGuide], { type: 'text/markdown' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'wiring_guide.md';
            a.click();
            URL.revokeObjectURL(url);
            this.log('Wiring guide downloaded', 'success');
        } else {
            this.log('No wiring guide to download. Generate guide first.', 'warning');
        }
    }

    updatePowerInfo() {
        const width = parseInt(document.getElementById('wiring-width').value);
        const height = parseInt(document.getElementById('wiring-height').value);
        const totalLeds = width * height;
        const maxCurrent = (totalLeds * 0.06).toFixed(2); // 60mA per LED
        const recommendedPSU = maxCurrent > 10 ? '20A' : maxCurrent > 5 ? '10A' : '5A';
        
        document.getElementById('power-info').innerHTML = `
            <div class="grid grid-2" style="gap: 15px;">
                <div>
                    <strong>Total LEDs:</strong> ${totalLeds}<br>
                    <strong>Max Current:</strong> ${maxCurrent}A<br>
                    <strong>Recommended PSU:</strong> 5V ${recommendedPSU}
                </div>
                <div>
                    <strong>Power Consumption:</strong> ${(maxCurrent * 5).toFixed(1)}W<br>
                    <strong>Strip Length:</strong> ${(totalLeds / 144).toFixed(1)}m<br>
                    <strong>Estimated Cost:</strong> $${(totalLeds * 0.1 + 50).toFixed(0)}
                </div>
            </div>
        `;
    }

    async saveConfig() {
        const config = {
            connectionMode: document.getElementById('connection-mode').value,
            serialPort: document.getElementById('serial-port').value,
            baudRate: parseInt(document.getElementById('baud-rate').value)
        };

        try {
            const response = await fetch(`${this.apiBase}/config`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(config)
            });

            if (response.ok) {
                this.log('Configuration saved', 'success');
            } else {
                throw new Error('Failed to save configuration');
            }
        } catch (error) {
            this.log(`Error saving config: ${error.message}`, 'error');
        }
    }

    async testConnection() {
        this.log('Testing connection...', 'warning');
        await this.checkConnection();
    }

    async loadConfig() {
        try {
            const response = await fetch(`${this.apiBase}/config`);
            if (response.ok) {
                const config = await response.json();
                document.getElementById('connection-mode').value = config.connectionMode || 'USB';
                document.getElementById('serial-port').value = config.serialPort || '';
                document.getElementById('baud-rate').value = config.baudRate || 115200;
            }
        } catch (error) {
            this.log(`Error loading config: ${error.message}`, 'error');
        }
    }

    async createBackup() {
        try {
            const response = await fetch(`${this.apiBase}/backup`, { method: 'POST' });
            if (response.ok) {
                const data = await response.json();
                this.log(`Backup created: ${data.filename}`, 'success');
                this.loadBackupList();
            }
        } catch (error) {
            this.log(`Error creating backup: ${error.message}`, 'error');
        }
    }

    async restoreBackup() {
        // This would show a file picker or backup list
        this.log('Restore functionality would be implemented here', 'warning');
    }

    async loadBackupList() {
        try {
            const response = await fetch(`${this.apiBase}/backups`);
            if (response.ok) {
                const backups = await response.json();
                let html = '<h4>Available Backups:</h4>';
                backups.forEach(backup => {
                    html += `<div style="margin: 5px 0; padding: 5px; background: rgba(0,0,0,0.3); border-radius: 4px;">${backup}</div>`;
                });
                document.getElementById('backup-list').innerHTML = html;
            }
        } catch (error) {
            this.log(`Error loading backups: ${error.message}`, 'error');
        }
    }

    async loadSystemStats() {
        try {
            const response = await fetch(`${this.apiBase}/system`);
            if (response.ok) {
                const stats = await response.json();
                document.getElementById('system-stats').innerHTML = `
                    <div class="grid grid-2" style="gap: 10px;">
                        <div><strong>CPU Usage:</strong> ${stats.cpu || 'N/A'}%</div>
                        <div><strong>Memory:</strong> ${stats.memory || 'N/A'}%</div>
                        <div><strong>Uptime:</strong> ${stats.uptime || 'N/A'}</div>
                        <div><strong>Temperature:</strong> ${stats.temperature || 'N/A'}°C</div>
                    </div>
                `;
            }
        } catch (error) {
            document.getElementById('system-stats').innerHTML = '<p>Unable to load system stats</p>';
        }
    }

    async loadHardwareInfo() {
        try {
            const response = await fetch(`${this.apiBase}/hardware`);
            if (response.ok) {
                const hardware = await response.json();
                document.getElementById('hardware-info').innerHTML = `
                    <div>
                        <strong>Controller:</strong> ${hardware.controller || 'Unknown'}<br>
                        <strong>Port:</strong> ${hardware.port || 'Not connected'}<br>
                        <strong>Baud Rate:</strong> ${hardware.baudRate || 'N/A'}<br>
                        <strong>Matrix Size:</strong> ${hardware.matrixSize || 'N/A'}
                    </div>
                `;
            }
        } catch (error) {
            document.getElementById('hardware-info').innerHTML = '<p>Unable to load hardware info</p>';
        }
    }

    log(message, type = 'info') {
        const logContainer = document.getElementById('activity-log');
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
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.matrixController = new MatrixController();
});