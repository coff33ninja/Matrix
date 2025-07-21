// LED Matrix Control Center - Main Application
class MatrixController {
    constructor() {
        // Always use absolute path for API regardless of base tag
        this.apiBase = '/api';
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
        document.getElementById('update-calculations').addEventListener('click', () => this.updatePowerCalculations());
        
        // Add event listeners for real-time updates
        ['wiring-width', 'wiring-height', 'leds-per-meter', 'power-supply', 'wiring-controller'].forEach(id => {
            const element = document.getElementById(id);
            if (element) {
                element.addEventListener('change', () => this.updatePowerCalculations());
            }
        });
        document.getElementById('wiring-width').addEventListener('input', () => this.updatePowerCalculations());
        document.getElementById('wiring-height').addEventListener('input', () => this.updatePowerCalculations());

        // Drawing section event listeners
        this.setupDrawingEventListeners();
        
        // Arduino section event listeners
        this.setupArduinoEventListeners();
        document.getElementById('leds-per-meter').addEventListener('change', () => this.updatePowerCalculations());
        document.getElementById('power-supply').addEventListener('change', () => this.updatePowerCalculations());

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
            case 'drawing':
                this.initializeDrawingData();
                this.updateSavedPatterns();
                break;
            case 'wiring':
                this.updatePowerInfo();
                break;
            case 'arduino':
                this.syncArduinoSettings();
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
        
        // Update power calculations when matrix size changes
        this.updatePowerCalculations();
    }

    // Power calculation methods
    updatePowerCalculations() {
        const width = parseInt(document.getElementById('wiring-width')?.value) || this.matrixSize.width;
        const height = parseInt(document.getElementById('wiring-height')?.value) || this.matrixSize.height;
        const ledsPerMeter = parseInt(document.getElementById('leds-per-meter')?.value) || 60;
        const powerSupply = document.getElementById('power-supply')?.value || '5V10A';
        
        const totalLeds = width * height;
        const stripLength = totalLeds / ledsPerMeter;
        const maxCurrentPerLed = 0.06; // 60mA per LED at full white
        const maxCurrent = totalLeds * maxCurrentPerLed;
        const maxPower = maxCurrent * 5; // 5V system
        
        // Parse power supply capacity
        const psuMatch = powerSupply.match(/(\d+)V(\d+)A/);
        const psuVoltage = psuMatch ? parseInt(psuMatch[1]) : 5;
        const psuCurrent = psuMatch ? parseInt(psuMatch[2]) : 10;
        const psuPower = psuVoltage * psuCurrent;
        
        // Calculate power usage percentage
        const powerPercentage = Math.min((maxPower / psuPower) * 100, 100);
        
        // Update display elements
        const elements = {
            'total-leds': totalLeds,
            'max-current': `${maxCurrent.toFixed(2)}A`,
            'recommended-psu': this.getRecommendedPSU(maxPower),
            'power-consumption': `${maxPower.toFixed(1)}W`,
            'estimated-cost': this.calculateEstimatedCost(totalLeds, stripLength, maxPower),
            'power-percentage': `${powerPercentage.toFixed(0)}%`
        };
        
        Object.entries(elements).forEach(([id, value]) => {
            const element = document.getElementById(id);
            if (element) element.textContent = value;
        });
        
        // Update power usage bar
        const powerBar = document.getElementById('power-usage-bar');
        if (powerBar) {
            powerBar.style.width = `${powerPercentage}%`;
            powerBar.style.background = powerPercentage > 80 ? 'var(--error)' : 
                                       powerPercentage > 60 ? 'var(--warning)' : 'var(--success)';
        }
        
        // Update shopping list
        this.updateShoppingList(totalLeds, stripLength, maxPower);
        
        // Update Mermaid diagram
        this.generateMermaidDiagram();
    }

    getRecommendedPSU(maxPower) {
        if (maxPower <= 20) return '5V 5A';
        if (maxPower <= 40) return '5V 10A';
        if (maxPower <= 80) return '5V 20A';
        if (maxPower <= 120) return '5V 30A';
        return '5V 40A';
    }

    calculateEstimatedCost(totalLeds, stripLength, maxPower) {
        const controller = document.getElementById('wiring-controller')?.value || 'arduino_uno';
        const controllerCost = this.getControllerPrice(controller);
        const stripCost = Math.ceil(stripLength) * 12; // $12 per meter
        const psuCost = this.getPSUCost(maxPower);
        const accessoriesCost = 15; // Level shifter, wires, etc.
        
        const total = controllerCost + stripCost + psuCost + accessoriesCost;
        return `$${total - 10}-${total + 10}`;
    }

    getControllerPrice(controller) {
        const prices = {
            'arduino_uno': 25,
            'arduino_nano': 15,
            'esp32': 12,
            'esp8266': 8
        };
        return prices[controller] || 25;
    }

    getPSUCost(maxPower) {
        if (maxPower <= 20) return 25;
        if (maxPower <= 40) return 35;
        if (maxPower <= 80) return 55;
        if (maxPower <= 120) return 75;
        return 95;
    }

    updateShoppingList(totalLeds, stripLength, maxPower) {
        const controller = document.getElementById('wiring-controller')?.value || 'arduino_uno';
        const controllerName = this.getControllerName(controller);
        const controllerPrice = this.getControllerPrice(controller);
        const stripPrice = Math.ceil(stripLength) * 12;
        const psuPrice = this.getPSUCost(maxPower);
        const recommendedPSU = this.getRecommendedPSU(maxPower);
        
        const items = [
            { name: controllerName, price: controllerPrice },
            { name: `WS2812B LED Strip (${Math.ceil(stripLength)}m)`, price: stripPrice },
            { name: `Power Supply ${recommendedPSU}`, price: psuPrice },
            { name: '74HCT125 Level Shifter', price: 3 },
            { name: 'Jumper Wires & Connectors', price: 8 },
            { name: 'Breadboard/Perfboard', price: 5 }
        ];
        
        const total = items.reduce((sum, item) => sum + item.price, 0);
        
        const listElement = document.getElementById('shopping-list');
        if (listElement) {
            listElement.innerHTML = `
                <ul>
                    ${items.map(item => `<li><span>${item.name}</span><span>$${item.price}</span></li>`).join('')}
                    <li><span><strong>Total Estimated Cost</strong></span><span><strong>$${total}</strong></span></li>
                </ul>
            `;
        }
    }

    getControllerName(controller) {
        const names = {
            'arduino_uno': 'Arduino Uno R3',
            'arduino_nano': 'Arduino Nano',
            'esp32': 'ESP32 Dev Board',
            'esp8266': 'ESP8266 NodeMCU'
        };
        return names[controller] || 'Arduino Uno R3';
    }

    // Mermaid diagram generation
    generateMermaidDiagram() {
        const controller = document.getElementById('wiring-controller')?.value || 'arduino_uno';
        const controllerName = this.getControllerName(controller);
        const dataPin = document.getElementById('data-pin')?.value || '6';
        const levelShifter = document.getElementById('level-shifter')?.value || '74hct125';
        
        let mermaidCode = '';
        
        if (levelShifter === 'none') {
            mermaidCode = `
                graph TD
                    A["🔌 Power Supply<br/>5V DC"] --> B["⚡ ${controllerName}"]
                    A --> C["💡 LED Strip<br/>VCC (5V)"]
                    B --> |"Pin ${dataPin}"| D["💡 LED Strip<br/>Data Input"]
                    B --> E["⚫ GND"]
                    A --> E
                    C --> E
                    
                    style A fill:#ff6b6b,stroke:#333,stroke-width:2px,color:#fff
                    style B fill:#4ecdc4,stroke:#333,stroke-width:2px,color:#fff
                    style C fill:#45b7d1,stroke:#333,stroke-width:2px,color:#fff
                    style D fill:#feca57,stroke:#333,stroke-width:2px,color:#333
                    style E fill:#2d3436,stroke:#333,stroke-width:2px,color:#fff
            `;
        } else {
            const shifterName = levelShifter === '74hct125' ? '74HCT125' : 
                              levelShifter === 'sn74lv1t34' ? 'SN74LV1T34' : 'Level Shifter';
            
            mermaidCode = `
                graph TD
                    A["🔌 Power Supply<br/>5V DC"] --> B["⚡ ${controllerName}"]
                    A --> C["💡 LED Strip<br/>VCC (5V)"]
                    B --> |"Pin ${dataPin}<br/>3.3V Logic"| D["🔄 ${shifterName}<br/>Level Shifter"]
                    D --> |"5V Logic"| E["💡 LED Strip<br/>Data Input"]
                    B --> F["⚫ GND"]
                    A --> F
                    C --> F
                    D --> F
                    G["🔋 Capacitor<br/>1000µF"] --> A
                    
                    style A fill:#ff6b6b,stroke:#333,stroke-width:2px,color:#fff
                    style B fill:#4ecdc4,stroke:#333,stroke-width:2px,color:#fff
                    style C fill:#45b7d1,stroke:#333,stroke-width:2px,color:#fff
                    style D fill:#96ceb4,stroke:#333,stroke-width:2px,color:#333
                    style E fill:#feca57,stroke:#333,stroke-width:2px,color:#333
                    style F fill:#2d3436,stroke:#333,stroke-width:2px,color:#fff
                    style G fill:#fd79a8,stroke:#333,stroke-width:2px,color:#fff
            `;
        }
        
        // Update the Mermaid diagram
        const diagramElement = document.getElementById('mermaid-diagram');
        if (diagramElement) {
            diagramElement.innerHTML = mermaidCode;
            
            // Re-initialize Mermaid if available
            if (typeof mermaid !== 'undefined') {
                mermaid.init(undefined, diagramElement);
            }
        }
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
        const width = parseInt(document.getElementById('wiring-width').value);
        const height = parseInt(document.getElementById('wiring-height').value);
        const ledsPerMeter = parseInt(document.getElementById('leds-per-meter').value);
        const powerSupply = document.getElementById('power-supply').value;

        this.log('Generating wiring guide...', 'warning');

        try {
            const response = await fetch(`${this.apiBase}/wiring`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    controller: controller,
                    width: width,
                    height: height,
                    ledsPerMeter: ledsPerMeter,
                    powerSupply: powerSupply
                })
            });

            if (response.ok) {
                const data = await response.json();
                this.log('Wiring guide generated successfully', 'success');
                this.wiringData = data.wiring;
                
                // Update power calculations with wiring data
                this.updatePowerCalculationsFromWiring(data.wiring);
                
                // Generate Mermaid diagram from backend
                this.displayMermaidDiagram(data.wiring.mermaidDiagram);
                
                // Update component list
                this.updateComponentListFromWiring(data.wiring);
            } else {
                throw new Error('Failed to generate wiring guide');
            }
        } catch (error) {
            this.log(`Error generating wiring: ${error.message}`, 'error');
        }
    }

    updatePowerCalculationsFromWiring(wiringData) {
        // Update power info display with data from backend
        const powerInfo = document.getElementById('power-info');
        if (powerInfo && wiringData.power) {
            powerInfo.innerHTML = `
                <div class="power-stat">
                    <span class="power-label">Total LEDs:</span>
                    <span class="power-value">${wiringData.matrix.totalLeds}</span>
                </div>
                <div class="power-stat">
                    <span class="power-label">Max Current:</span>
                    <span class="power-value">${wiringData.power.maxCurrent}A</span>
                </div>
                <div class="power-stat">
                    <span class="power-label">Max Power:</span>
                    <span class="power-value">${wiringData.power.maxPower}W</span>
                </div>
                <div class="power-stat">
                    <span class="power-label">Recommended PSU:</span>
                    <span class="power-value">${wiringData.power.recommendedPSU}</span>
                </div>
                <div class="power-stat">
                    <span class="power-label">Strip Length:</span>
                    <span class="power-value">${wiringData.strip.totalLength}m</span>
                </div>
            `;
        }
    }
    
    displayMermaidDiagram(mermaidCode) {
        const diagramElement = document.getElementById('mermaid-diagram');
        if (diagramElement && mermaidCode) {
            // Create a container with controls
            diagramElement.innerHTML = `
                <div class="mermaid-container">
                    <div class="mermaid-controls">
                        <button class="mermaid-control-btn" onclick="this.parentElement.parentElement.querySelector('.mermaid').style.transform = 'scale(' + (parseFloat(this.parentElement.parentElement.querySelector('.mermaid').style.transform.match(/scale\\(([^)]+)\\)/)?.[1] || 1) * 1.2 + ')'" title="Zoom In">
                            🔍+
                        </button>
                        <button class="mermaid-control-btn" onclick="this.parentElement.parentElement.querySelector('.mermaid').style.transform = 'scale(' + (parseFloat(this.parentElement.parentElement.querySelector('.mermaid').style.transform.match(/scale\\(([^)]+)\\)/)?.[1] || 1) * 0.8 + ')'" title="Zoom Out">
                            🔍-
                        </button>
                        <button class="mermaid-control-btn" onclick="this.parentElement.parentElement.querySelector('.mermaid').style.transform = 'scale(1)'" title="Reset Zoom">
                            ↻
                        </button>
                        <button class="mermaid-control-btn" onclick="matrixController.downloadDiagramPNG(this)" title="Download PNG">
                            📥 PNG
                        </button>
                    </div>
                    <div class="mermaid">${mermaidCode}</div>
                </div>
            `;
            
            // Re-initialize Mermaid if available
            if (typeof mermaid !== 'undefined') {
                mermaid.init(undefined, diagramElement.querySelector('.mermaid'));
            }
        }
    }
    
    updateComponentListFromWiring(wiringData) {
        const componentList = document.getElementById('component-list');
        if (componentList && wiringData.components) {
            let html = '<div class="component-grid">';
            
            wiringData.components.forEach(component => {
                html += `
                    <div class="component-item">
                        <strong>${component.name}</strong>
                        <span>Qty: ${component.quantity}</span>
                        <small>${component.type}</small>
                    </div>
                `;
            });
            
            html += '</div>';
            
            if (wiringData.estimatedCost) {
                html += `
                    <div class="cost-summary">
                        <strong>Estimated Total Cost: $${wiringData.estimatedCost}</strong>
                    </div>
                `;
            }
            
            componentList.innerHTML = html;
        }
    }
    
    downloadDiagramPNG(button) {
        const container = button.closest('.mermaid-container');
        const svg = container.querySelector('svg');
        if (svg) {
            // Create a canvas element
            const canvas = document.createElement('canvas');
            const ctx = canvas.getContext('2d');
            
            // Get SVG dimensions
            const svgRect = svg.getBoundingClientRect();
            const svgData = new XMLSerializer().serializeToString(svg);
            
            // Set canvas size with higher resolution for better quality
            const scale = 2;
            canvas.width = svgRect.width * scale;
            canvas.height = svgRect.height * scale;
            
            // Create image from SVG
            const img = new Image();
            const svgBlob = new Blob([svgData], { type: 'image/svg+xml;charset=utf-8' });
            const url = URL.createObjectURL(svgBlob);
            
            img.onload = function() {
                // Set white background
                ctx.fillStyle = '#ffffff';
                ctx.fillRect(0, 0, canvas.width, canvas.height);
                
                // Scale context for higher resolution
                ctx.scale(scale, scale);
                
                // Draw the SVG image
                ctx.drawImage(img, 0, 0, svgRect.width, svgRect.height);
                
                // Convert canvas to PNG and download
                canvas.toBlob(function(blob) {
                    const pngUrl = URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = pngUrl;
                    a.download = 'led-matrix-wiring-diagram.png';
                    a.click();
                    URL.revokeObjectURL(pngUrl);
                }, 'image/png');
                
                URL.revokeObjectURL(url);
            };
            
            img.src = url;
        }
    }

    setupDrawingEventListeners() {
        // Drawing mode and tools
        document.getElementById('drawing-mode').addEventListener('change', (e) => {
            this.drawingMode = e.target.value;
            this.updateDrawingCursor();
        });
        
        document.getElementById('brush-color').addEventListener('change', (e) => {
            this.brushColor = e.target.value;
        });
        
        document.getElementById('brush-size').addEventListener('input', (e) => {
            this.brushSize = parseInt(e.target.value);
            document.getElementById('brush-size-display').textContent = `${this.brushSize}x${this.brushSize}`;
        });
        
        // Color presets
        document.querySelectorAll('.color-preset').forEach(preset => {
            preset.addEventListener('click', (e) => {
                const color = e.target.dataset.color;
                this.brushColor = color;
                document.getElementById('brush-color').value = color;
                
                // Update active preset
                document.querySelectorAll('.color-preset').forEach(p => p.classList.remove('active'));
                e.target.classList.add('active');
            });
        });
        
        // Drawing actions
        document.getElementById('clear-drawing').addEventListener('click', () => this.clearDrawing());
        document.getElementById('fill-all').addEventListener('click', () => this.fillAll());
        document.getElementById('save-pattern').addEventListener('click', () => this.savePattern());
        document.getElementById('load-pattern').addEventListener('click', () => this.loadPattern());
        document.getElementById('send-to-matrix').addEventListener('click', () => this.sendDrawingToMatrix());
        
        // Pattern library
        document.querySelectorAll('.pattern-item').forEach(item => {
            item.addEventListener('click', (e) => {
                const pattern = e.currentTarget.dataset.pattern;
                this.loadPresetPattern(pattern);
            });
        });
        
        // Initialize drawing state
        this.drawingMode = 'paint';
        this.brushColor = '#e94560';
        this.brushSize = 1;
        this.isDrawing = false;
        this.drawingData = [];
        this.savedPatterns = JSON.parse(localStorage.getItem('ledMatrixPatterns') || '[]');
        
        // Initialize drawing data structure
        this.initializeDrawingData();
        
        this.setupMatrixDrawing();
        this.updateSavedPatterns();
    }
    
    setupArduinoEventListeners() {
        document.getElementById('arduino-brightness').addEventListener('input', (e) => {
            document.getElementById('arduino-brightness-display').textContent = e.target.value;
        });
        
        document.getElementById('arduino-board').addEventListener('change', () => {
            this.syncArduinoSettings();
        });
        
        document.getElementById('generate-arduino').addEventListener('click', () => this.generateArduinoPackage());
        document.getElementById('preview-code').addEventListener('click', () => this.previewArduinoCode());
        document.getElementById('download-package').addEventListener('click', () => this.downloadArduinoPackage());
        document.getElementById('copy-code').addEventListener('click', () => this.copyArduinoCode());
        document.getElementById('download-ino').addEventListener('click', () => this.downloadArduinoFile());
    }
    
    setupMatrixDrawing() {
        const pixels = document.querySelectorAll('.led-pixel');
        
        pixels.forEach((pixel, index) => {
            // Mouse events for drawing
            pixel.addEventListener('mousedown', (e) => {
                e.preventDefault();
                this.isDrawing = true;
                this.drawPixel(index);
            });
            
            pixel.addEventListener('mouseenter', (e) => {
                if (this.isDrawing) {
                    this.drawPixel(index);
                }
            });
            
            pixel.addEventListener('mouseup', () => {
                this.isDrawing = false;
            });
            
            // Touch events for mobile
            pixel.addEventListener('touchstart', (e) => {
                e.preventDefault();
                this.isDrawing = true;
                this.drawPixel(index);
            });
            
            pixel.addEventListener('touchmove', (e) => {
                e.preventDefault();
                if (this.isDrawing) {
                    const touch = e.touches[0];
                    const element = document.elementFromPoint(touch.clientX, touch.clientY);
                    if (element && element.classList.contains('led-pixel')) {
                        const touchIndex = parseInt(element.dataset.index);
                        this.drawPixel(touchIndex);
                    }
                }
            });
            
            pixel.addEventListener('touchend', () => {
                this.isDrawing = false;
            });
        });
        
        // Prevent context menu on right click
        document.getElementById('matrix-preview').addEventListener('contextmenu', (e) => {
            e.preventDefault();
        });
        
        // Stop drawing when mouse leaves the matrix
        document.getElementById('matrix-preview').addEventListener('mouseleave', () => {
            this.isDrawing = false;
        });
        
        // Initialize drawing data
        this.initializeDrawingData();
    }
    
    initializeDrawingData() {
        const width = this.matrixSize.width;
        const height = this.matrixSize.height;
        this.drawingData = Array(height).fill().map(() => Array(width).fill('#000000'));
    }
    
    drawPixel(index) {
        const width = this.matrixSize.width;
        const height = this.matrixSize.height;
        const x = index % width;
        const y = Math.floor(index / width);
        
        if (this.drawingMode === 'paint') {
            this.paintPixels(x, y);
        } else if (this.drawingMode === 'erase') {
            this.erasePixels(x, y);
        } else if (this.drawingMode === 'fill') {
            this.fillArea(x, y);
        }
    }
    
    paintPixels(centerX, centerY) {
        const width = this.matrixSize.width;
        const height = this.matrixSize.height;
        const size = this.brushSize;
        const offset = Math.floor(size / 2);
        
        for (let dy = -offset; dy <= offset; dy++) {
            for (let dx = -offset; dx <= offset; dx++) {
                const x = centerX + dx;
                const y = centerY + dy;
                
                if (x >= 0 && x < width && y >= 0 && y < height) {
                    const index = y * width + x;
                    const pixel = document.querySelector(`[data-index="${index}"]`);
                    
                    if (pixel) {
                        pixel.style.backgroundColor = this.brushColor;
                        this.drawingData[y][x] = this.brushColor;
                    }
                }
            }
        }
    }
    
    erasePixels(centerX, centerY) {
        const width = this.matrixSize.width;
        const height = this.matrixSize.height;
        const size = this.brushSize;
        const offset = Math.floor(size / 2);
        
        for (let dy = -offset; dy <= offset; dy++) {
            for (let dx = -offset; dx <= offset; dx++) {
                const x = centerX + dx;
                const y = centerY + dy;
                
                if (x >= 0 && x < width && y >= 0 && y < height) {
                    const index = y * width + x;
                    const pixel = document.querySelector(`[data-index="${index}"]`);
                    
                    if (pixel) {
                        pixel.style.backgroundColor = '#333';
                        this.drawingData[y][x] = '#000000';
                    }
                }
            }
        }
    }
    
    fillArea(startX, startY) {
        const width = this.matrixSize.width;
        const height = this.matrixSize.height;
        const targetColor = this.drawingData[startY][startX];
        const fillColor = this.brushColor;
        
        if (targetColor === fillColor) return;
        
        const stack = [[startX, startY]];
        
        while (stack.length > 0) {
            const [x, y] = stack.pop();
            
            if (x < 0 || x >= width || y < 0 || y >= height) continue;
            if (this.drawingData[y][x] !== targetColor) continue;
            
            this.drawingData[y][x] = fillColor;
            const index = y * width + x;
            const pixel = document.querySelector(`[data-index="${index}"]`);
            if (pixel) {
                pixel.style.backgroundColor = fillColor;
            }
            
            stack.push([x + 1, y], [x - 1, y], [x, y + 1], [x, y - 1]);
        }
    }
    
    clearDrawing() {
        const pixels = document.querySelectorAll('.led-pixel');
        pixels.forEach(pixel => {
            pixel.style.backgroundColor = '#333';
        });
        this.initializeDrawingData();
        this.log('Drawing cleared', 'success');
    }
    
    fillAll() {
        const pixels = document.querySelectorAll('.led-pixel');
        pixels.forEach((pixel, index) => {
            pixel.style.backgroundColor = this.brushColor;
            const x = index % this.matrixSize.width;
            const y = Math.floor(index / this.matrixSize.width);
            this.drawingData[y][x] = this.brushColor;
        });
        this.log('Matrix filled with color', 'success');
    }
    
    savePattern() {
        const name = prompt('Enter pattern name:');
        if (!name) return;
        
        const pattern = {
            name: name,
            width: this.matrixSize.width,
            height: this.matrixSize.height,
            data: JSON.parse(JSON.stringify(this.drawingData)),
            timestamp: new Date().toISOString()
        };
        
        this.savedPatterns.push(pattern);
        localStorage.setItem('ledMatrixPatterns', JSON.stringify(this.savedPatterns));
        this.updateSavedPatterns();
        this.log(`Pattern "${name}" saved`, 'success');
    }
    
    loadPattern() {
        const input = document.createElement('input');
        input.type = 'file';
        input.accept = '.json';
        input.onchange = (e) => {
            const file = e.target.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = (e) => {
                    try {
                        const pattern = JSON.parse(e.target.result);
                        this.applyPattern(pattern);
                        this.log(`Pattern "${pattern.name}" loaded`, 'success');
                    } catch (error) {
                        this.log('Error loading pattern file', 'error');
                    }
                };
                reader.readAsText(file);
            }
        };
        input.click();
    }
    
    applyPattern(pattern) {
        if (pattern.width !== this.matrixSize.width || pattern.height !== this.matrixSize.height) {
            if (!confirm('Pattern size doesn\'t match current matrix. Apply anyway?')) {
                return;
            }
        }
        
        this.clearDrawing();
        
        for (let y = 0; y < Math.min(pattern.height, this.matrixSize.height); y++) {
            for (let x = 0; x < Math.min(pattern.width, this.matrixSize.width); x++) {
                const color = pattern.data[y][x];
                if (color !== '#000000') {
                    const index = y * this.matrixSize.width + x;
                    const pixel = document.querySelector(`[data-index="${index}"]`);
                    if (pixel) {
                        pixel.style.backgroundColor = color;
                        this.drawingData[y][x] = color;
                    }
                }
            }
        }
    }
    
    loadPresetPattern(patternName) {
        const patterns = {
            smiley: this.generateSmileyPattern(),
            heart: this.generateHeartPattern(),
            arrow: this.generateArrowPattern(),
            star: this.generateStarPattern(),
            checkerboard: this.generateCheckerboardPattern(),
            border: this.generateBorderPattern()
        };
        
        if (patterns[patternName]) {
            this.applyPattern(patterns[patternName]);
            this.log(`Applied ${patternName} pattern`, 'success');
        }
    }
    
    generateSmileyPattern() {
        const width = this.matrixSize.width;
        const height = this.matrixSize.height;
        const data = Array(height).fill().map(() => Array(width).fill('#000000'));
        
        // Simple smiley face for 16x16 matrix
        if (width >= 16 && height >= 16) {
            const centerX = Math.floor(width / 2);
            const centerY = Math.floor(height / 2);
            
            // Eyes
            data[centerY - 3][centerX - 3] = '#ffff00';
            data[centerY - 3][centerX + 3] = '#ffff00';
            
            // Mouth
            for (let x = centerX - 3; x <= centerX + 3; x++) {
                data[centerY + 2][x] = '#ffff00';
            }
            data[centerY + 1][centerX - 2] = '#ffff00';
            data[centerY + 1][centerX + 2] = '#ffff00';
        }
        
        return { name: 'Smiley', width, height, data };
    }
    
    generateHeartPattern() {
        const width = this.matrixSize.width;
        const height = this.matrixSize.height;
        const data = Array(height).fill().map(() => Array(width).fill('#000000'));
        
        // Simple heart pattern
        const centerX = Math.floor(width / 2);
        const centerY = Math.floor(height / 2);
        
        // Heart shape
        const heartPoints = [
            [centerX, centerY + 2],
            [centerX - 1, centerY + 1], [centerX + 1, centerY + 1],
            [centerX - 2, centerY], [centerX + 2, centerY],
            [centerX - 2, centerY - 1], [centerX + 2, centerY - 1],
            [centerX - 1, centerY - 2], [centerX + 1, centerY - 2]
        ];
        
        heartPoints.forEach(([x, y]) => {
            if (x >= 0 && x < width && y >= 0 && y < height) {
                data[y][x] = '#ff0000';
            }
        });
        
        return { name: 'Heart', width, height, data };
    }
    
    generateArrowPattern() {
        const width = this.matrixSize.width;
        const height = this.matrixSize.height;
        const data = Array(height).fill().map(() => Array(width).fill('#000000'));
        
        const centerY = Math.floor(height / 2);
        
        // Arrow pointing right
        for (let x = 2; x < width - 2; x++) {
            data[centerY][x] = '#00ff00';
        }
        
        // Arrow head
        for (let i = 1; i <= 3; i++) {
            data[centerY - i][width - 2 - i] = '#00ff00';
            data[centerY + i][width - 2 - i] = '#00ff00';
        }
        
        return { name: 'Arrow', width, height, data };
    }
    
    generateStarPattern() {
        const width = this.matrixSize.width;
        const height = this.matrixSize.height;
        const data = Array(height).fill().map(() => Array(width).fill('#000000'));
        
        const centerX = Math.floor(width / 2);
        const centerY = Math.floor(height / 2);
        
        // Simple star pattern
        const starPoints = [
            [centerX, centerY - 3],
            [centerX - 1, centerY - 1], [centerX + 1, centerY - 1],
            [centerX - 3, centerY], [centerX + 3, centerY],
            [centerX - 2, centerY + 1], [centerX + 2, centerY + 1],
            [centerX, centerY + 3]
        ];
        
        starPoints.forEach(([x, y]) => {
            if (x >= 0 && x < width && y >= 0 && y < height) {
                data[y][x] = '#ffff00';
            }
        });
        
        return { name: 'Star', width, height, data };
    }
    
    generateCheckerboardPattern() {
        const width = this.matrixSize.width;
        const height = this.matrixSize.height;
        const data = Array(height).fill().map(() => Array(width).fill('#000000'));
        
        for (let y = 0; y < height; y++) {
            for (let x = 0; x < width; x++) {
                if ((x + y) % 2 === 0) {
                    data[y][x] = '#ffffff';
                }
            }
        }
        
        return { name: 'Checkerboard', width, height, data };
    }
    
    generateBorderPattern() {
        const width = this.matrixSize.width;
        const height = this.matrixSize.height;
        const data = Array(height).fill().map(() => Array(width).fill('#000000'));
        
        // Top and bottom borders
        for (let x = 0; x < width; x++) {
            data[0][x] = '#0000ff';
            data[height - 1][x] = '#0000ff';
        }
        
        // Left and right borders
        for (let y = 0; y < height; y++) {
            data[y][0] = '#0000ff';
            data[y][width - 1] = '#0000ff';
        }
        
        return { name: 'Border', width, height, data };
    }
    
    updateSavedPatterns() {
        const container = document.getElementById('saved-patterns');
        
        if (this.savedPatterns.length === 0) {
            container.innerHTML = '<p>No saved patterns yet. Create and save your first pattern!</p>';
            return;
        }
        
        container.innerHTML = '';
        
        this.savedPatterns.forEach((pattern, index) => {
            const patternDiv = document.createElement('div');
            patternDiv.className = 'saved-pattern';
            patternDiv.innerHTML = `
                <div class="saved-pattern-preview" id="preview-${index}"></div>
                <span>${pattern.name}</span>
                <small>${new Date(pattern.timestamp).toLocaleDateString()}</small>
            `;
            
            patternDiv.addEventListener('click', () => {
                this.applyPattern(pattern);
                this.log(`Applied pattern "${pattern.name}"`, 'success');
            });
            
            container.appendChild(patternDiv);
            
            // Generate mini preview
            this.generatePatternPreview(pattern, `preview-${index}`);
        });
    }
    
    generatePatternPreview(pattern, containerId) {
        const container = document.getElementById(containerId);
        if (!container) return;
        
        container.innerHTML = '';
        
        const scaleX = 80 / pattern.width;
        const scaleY = 80 / pattern.height;
        const pixelSize = Math.min(scaleX, scaleY);
        
        for (let y = 0; y < pattern.height; y++) {
            for (let x = 0; x < pattern.width; x++) {
                const color = pattern.data[y][x];
                if (color !== '#000000') {
                    const pixel = document.createElement('div');
                    pixel.className = 'saved-pattern-pixel';
                    pixel.style.left = `${x * pixelSize}px`;
                    pixel.style.top = `${y * pixelSize}px`;
                    pixel.style.width = `${pixelSize}px`;
                    pixel.style.height = `${pixelSize}px`;
                    pixel.style.backgroundColor = color;
                    container.appendChild(pixel);
                }
            }
        }
    }
    
    async sendDrawingToMatrix() {
        try {
            const matrixData = this.convertDrawingToMatrixData();
            
            const response = await fetch(`${this.apiBase}/pattern`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    pattern: 'custom',
                    data: matrixData,
                    brightness: this.brightness || 128,
                    speed: this.speed || 50
                })
            });
            
            if (response.ok) {
                this.log('Drawing sent to matrix', 'success');
            } else {
                throw new Error('Failed to send drawing to matrix');
            }
        } catch (error) {
            this.log(`Error sending drawing: ${error.message}`, 'error');
        }
    }
    
    convertDrawingToMatrixData() {
        const width = this.matrixSize.width;
        const height = this.matrixSize.height;
        const matrixData = [];
        
        for (let y = 0; y < height; y++) {
            const row = [];
            for (let x = 0; x < width; x++) {
                const color = this.drawingData[y][x];
                const rgb = this.hexToRgb(color);
                row.push([rgb.r, rgb.g, rgb.b]);
            }
            matrixData.push(row);
        }
        
        return matrixData;
    }
    
    hexToRgb(hex) {
        const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
        return result ? {
            r: parseInt(result[1], 16),
            g: parseInt(result[2], 16),
            b: parseInt(result[3], 16)
        } : { r: 0, g: 0, b: 0 };
    }
    
    updateDrawingCursor() {
        const pixels = document.querySelectorAll('.led-pixel');
        const cursors = {
            paint: 'crosshair',
            erase: 'grab',
            fill: 'pointer',
            line: 'crosshair',
            rectangle: 'crosshair',
            circle: 'crosshair'
        };
        
        pixels.forEach(pixel => {
            pixel.style.cursor = cursors[this.drawingMode] || 'crosshair';
        });
    }

    updatePowerCalculations(data = null) {
        const width = parseInt(document.getElementById('wiring-width').value);
        const height = parseInt(document.getElementById('wiring-height').value);
        const ledsPerMeter = parseInt(document.getElementById('leds-per-meter').value);
        
        const totalLeds = width * height;
        const maxCurrentPerLed = 0.06; // 60mA per LED at full white
        const maxCurrent = totalLeds * maxCurrentPerLed;
        const maxPower = maxCurrent * 5; // 5V system
        const stripLength = totalLeds / ledsPerMeter;
        
        // Update display
        document.getElementById('total-leds').textContent = totalLeds;
        document.getElementById('max-current').textContent = `${maxCurrent.toFixed(2)}A`;
        document.getElementById('max-power').textContent = `${maxPower.toFixed(1)}W`;
        document.getElementById('strip-length').textContent = `${stripLength.toFixed(2)}m`;
        
        // Recommend power supply
        let recommendedPsu = '5V2A';
        if (maxPower > 80) recommendedPsu = '5V20A';
        else if (maxPower > 40) recommendedPsu = '5V10A';
        else if (maxPower > 20) recommendedPsu = '5V5A';
        
        document.getElementById('recommended-psu').textContent = recommendedPsu;
        
        // Update power supply selection if needed
        const psuSelect = document.getElementById('power-supply');
        const currentPsu = psuSelect.value;
        const currentWatts = this.getPowerSupplyWatts(currentPsu);
        
        if (currentWatts < maxPower) {
            // Highlight insufficient power supply
            psuSelect.style.borderColor = '#ef4444';
            psuSelect.style.backgroundColor = 'rgba(239, 68, 68, 0.1)';
        } else {
            psuSelect.style.borderColor = '';
            psuSelect.style.backgroundColor = '';
        }
    }

    getPowerSupplyWatts(psuValue) {
        const wattsMap = {
            '5V2A': 10,
            '5V5A': 25,
            '5V10A': 50,
            '5V20A': 100,
            '5V30A': 150,
            '5V40A': 200
        };
        return wattsMap[psuValue] || 10;
    }

    async generateMermaidDiagram(data) {
        const controller = document.getElementById('wiring-controller').value;
        const width = parseInt(document.getElementById('wiring-width').value);
        const height = parseInt(document.getElementById('wiring-height').value);
        const dataPin = document.getElementById('data-pin')?.value || 6;
        
        // Create Mermaid diagram
        const mermaidCode = this.createMermaidWiringDiagram(controller, width, height, dataPin);
        
        // Initialize Mermaid if not already done
        if (typeof mermaid !== 'undefined') {
            mermaid.initialize({ 
                startOnLoad: false,
                theme: 'dark',
                themeVariables: {
                    primaryColor: '#1a1a2e',
                    primaryTextColor: '#f1f1f1',
                    primaryBorderColor: '#e94560',
                    lineColor: '#e94560',
                    secondaryColor: '#16213e',
                    tertiaryColor: '#0f3460'
                }
            });
            
            try {
                const diagramDiv = document.getElementById('mermaid-diagram');
                diagramDiv.innerHTML = `<div class="mermaid">${mermaidCode}</div>`;
                await mermaid.run();
            } catch (error) {
                console.error('Mermaid rendering error:', error);
                document.getElementById('mermaid-diagram').innerHTML = 
                    `<p style="color: #ef4444;">Error rendering diagram: ${error.message}</p>`;
            }
        } else {
            document.getElementById('mermaid-diagram').innerHTML = 
                '<p style="color: #fbbf24;">Mermaid library not loaded</p>';
        }
    }

    createMermaidWiringDiagram(controller, width, height, dataPin) {
        const totalLeds = width * height;
        const controllerName = controller.replace('_', ' ').toUpperCase();
        
        return `
graph TD
    PSU[Power Supply<br/>5V DC] --> |+5V Red| LED1[LED Strip<br/>${totalLeds} LEDs]
    PSU --> |GND Black| LED1
    PSU --> |+5V Red| MCU[${controllerName}]
    PSU --> |GND Black| MCU
    
    MCU --> |Pin ${dataPin}<br/>Data Green| LED1
    MCU --> |GND Black| LED1
    
    LED1 --> |Data Out| LED2[Additional Strips<br/>if needed]
    
    %% Styling
    classDef psu fill:#ff6b6b,stroke:#ff5252,stroke-width:2px,color:#fff
    classDef mcu fill:#4ecdc4,stroke:#26a69a,stroke-width:2px,color:#fff  
    classDef led fill:#ffd93d,stroke:#ffc107,stroke-width:2px,color:#000
    
    class PSU psu
    class MCU mcu
    class LED1,LED2 led
        `;
    }

    updateComponentList(data) {
        const controller = document.getElementById('wiring-controller').value;
        const width = parseInt(document.getElementById('wiring-width').value);
        const height = parseInt(document.getElementById('wiring-height').value);
        const ledsPerMeter = parseInt(document.getElementById('leds-per-meter').value);
        const powerSupply = document.getElementById('power-supply').value;
        
        const totalLeds = width * height;
        const stripLength = Math.ceil(totalLeds / ledsPerMeter);
        
        // Component pricing (approximate)
        const components = [
            {
                name: controller.replace('_', ' ').toUpperCase(),
                quantity: 1,
                price: this.getControllerPrice(controller),
                description: 'Microcontroller board'
            },
            {
                name: `WS2812B LED Strip (${ledsPerMeter} LEDs/m)`,
                quantity: stripLength,
                price: this.getStripPrice(ledsPerMeter) * stripLength,
                description: `${stripLength}m of LED strip`
            },
            {
                name: powerSupply.replace('V', 'V ').replace('A', 'A Power Supply'),
                quantity: 1,
                price: this.getPowerSupplyPrice(powerSupply),
                description: 'Switching power supply'
            },
            {
                name: 'Jumper Wires',
                quantity: 1,
                price: 5,
                description: 'Male-to-male jumper wires'
            },
            {
                name: 'Breadboard (optional)',
                quantity: 1,
                price: 8,
                description: 'For prototyping connections'
            },
            {
                name: '1000µF Capacitor',
                quantity: 1,
                price: 3,
                description: 'Power supply smoothing'
            },
            {
                name: '470Ω Resistor',
                quantity: 1,
                price: 1,
                description: 'Data line protection'
            }
        ];
        
        const totalCost = components.reduce((sum, comp) => sum + comp.price, 0);
        
        let html = '<div class="grid grid-2" style="gap: 10px; margin-bottom: 15px;">';
        components.forEach(comp => {
            html += `
                <div style="display: flex; justify-content: space-between; padding: 8px; background: rgba(15, 52, 96, 0.2); border-radius: 5px;">
                    <div>
                        <strong>${comp.name}</strong><br>
                        <small style="color: var(--text-muted);">${comp.description}</small>
                    </div>
                    <div style="text-align: right;">
                        <div>Qty: ${comp.quantity}</div>
                        <div style="color: var(--success);">$${comp.price}</div>
                    </div>
                </div>
            `;
        });
        html += '</div>';
        
        html += `
            <div style="text-align: center; padding: 15px; background: rgba(233, 69, 96, 0.1); border-radius: 8px; border: 1px solid rgba(233, 69, 96, 0.3);">
                <strong style="font-size: 1.2em; color: var(--highlight);">Total Estimated Cost: $${totalCost}</strong>
                <br><small style="color: var(--text-muted);">Prices are approximate and may vary by supplier</small>
            </div>
        `;
        
        document.getElementById('component-list').innerHTML = html;
    }

    getControllerPrice(controller) {
        const prices = {
            'arduino_uno': 25,
            'arduino_nano': 15,
            'esp32': 12,
            'esp8266': 8
        };
        return prices[controller] || 20;
    }

    getStripPrice(ledsPerMeter) {
        const prices = {
            30: 15,
            60: 25,
            144: 45,
            256: 80
        };
        return prices[ledsPerMeter] || 25;
    }

    getPowerSupplyPrice(powerSupply) {
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

    downloadWiring() {
        if (this.wiringData) {
            // Generate markdown content from wiring data
            const markdown = this.generateWiringMarkdown(this.wiringData);
            const blob = new Blob([markdown], { type: 'text/markdown' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `wiring_guide_${this.wiringData.controller}_${this.wiringData.matrix.width}x${this.wiringData.matrix.height}.md`;
            a.click();
            URL.revokeObjectURL(url);
            this.log('Wiring guide downloaded', 'success');
        } else {
            this.log('No wiring guide to download. Generate guide first.', 'warning');
        }
    }
    
    generateWiringMarkdown(wiringData) {
        const date = new Date().toISOString().split('T')[0];
        return `# LED Matrix Wiring Guide
# ${wiringData.matrix.width}×${wiringData.matrix.height} Matrix with ${wiringData.controller}

Generated on: ${date}

## Configuration Summary:
- Controller: ${wiringData.controller}
- Matrix Size: ${wiringData.matrix.width}×${wiringData.matrix.height} (${wiringData.matrix.totalLeds} LEDs)
- Maximum Current: ${wiringData.power.maxCurrent}A
- Maximum Power: ${wiringData.power.maxPower}W
- Recommended PSU: ${wiringData.power.recommendedPSU}
- Selected PSU: ${wiringData.power.selectedPSU}

## Mermaid Wiring Diagram:
\`\`\`mermaid
${wiringData.mermaidDiagram}
\`\`\`

## Component List:
${wiringData.components.map(comp => `- **${comp.name}** (${comp.quantity}) - ${comp.type}`).join('\n')}

## Estimated Cost:
**Total: $${wiringData.estimatedCost}**

## Strip Configuration:
- LEDs per meter: ${wiringData.strip.ledsPerMeter}
- Total length needed: ${wiringData.strip.totalLength}m
- Suggested segments: ${wiringData.strip.segments}

---
Generated by LED Matrix Control Center
`;
    }

    // Arduino Package Generation Methods
    async generateArduinoPackage() {
        const board = document.getElementById('arduino-board').value;
        const dataPin = parseInt(document.getElementById('arduino-data-pin').value);
        const width = parseInt(document.getElementById('arduino-width').value);
        const height = parseInt(document.getElementById('arduino-height').value);
        const brightness = parseInt(document.getElementById('arduino-brightness').value);
        
        const includePatterns = document.getElementById('include-patterns').checked;
        const includeWiring = document.getElementById('include-wiring').checked;
        const includeLibraries = document.getElementById('include-libraries').checked;
        const includeReadme = document.getElementById('include-readme').checked;
        
        this.log('Generating Arduino package...', 'warning');
        
        try {
            // Use existing Arduino generation API
            const response = await fetch(`${this.apiBase}/generate`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    board: board,
                    width: width,
                    height: height,
                    data_pin: dataPin,
                    brightness: brightness
                })
            });
            
            if (!response.ok) {
                throw new Error('Failed to generate Arduino code');
            }
            
            const result = await response.json();
            let arduinoCode = result.code;
            
            // Enhance the generated code with custom patterns if requested
            if (includePatterns && this.savedPatterns.length > 0) {
                arduinoCode = this.enhanceArduinoCodeWithPatterns(arduinoCode);
            }
            
            // Generate package contents
            this.arduinoPackage = {
                code: arduinoCode,
                board: board,
                config: { dataPin, width, height, brightness },
                patterns: includePatterns ? this.savedPatterns : [],
                wiring: includeWiring ? this.wiringData : null,
                includeLibraries,
                includeReadme
            };
            
            this.updatePackageContents();
            this.log('Arduino package generated successfully', 'success');
            
        } catch (error) {
            this.log(`Error generating Arduino package: ${error.message}`, 'error');
        }
    }
    
    enhanceArduinoCodeWithPatterns(baseCode) {
        if (!this.savedPatterns || this.savedPatterns.length === 0) {
            return baseCode;
        }
        
        // Find the loop function and add custom pattern cases
        let enhancedCode = baseCode;
        
        // Look for the switch statement in the loop function
        const switchPattern = /switch\s*\([^)]+\)\s*{[^}]*}/;
        const switchMatch = enhancedCode.match(switchPattern);
        
        if (switchMatch) {
            let switchStatement = switchMatch[0];
            
            // Add custom pattern cases before the default case
            let customCases = '';
            this.savedPatterns.forEach((pattern, index) => {
                // Find the highest case number and add after it
                const caseNumbers = switchStatement.match(/case\s+(\d+):/g);
                const maxCase = Math.max(...caseNumbers.map(c => parseInt(c.match(/\d+/)[0])));
                customCases += `\n    case ${maxCase + 1 + index}: customPattern${index}(); break;`;
            });
            
            // Insert custom cases before the default case
            const defaultIndex = switchStatement.indexOf('default:');
            if (defaultIndex !== -1) {
                switchStatement = switchStatement.slice(0, defaultIndex) + 
                                customCases + '\n    ' + 
                                switchStatement.slice(defaultIndex);
            }
            
            enhancedCode = enhancedCode.replace(switchMatch[0], switchStatement);
        }
        
        // Add custom pattern functions at the end
        let customFunctions = '\n\n// Custom Pattern Functions\n';
        this.savedPatterns.forEach((pattern, index) => {
            customFunctions += `\nvoid customPattern${index}() {\n`;
            customFunctions += `  // Pattern: ${pattern.name}\n`;
            customFunctions += `  // Size: ${pattern.width}x${pattern.height}\n`;
            customFunctions += `  FastLED.clear();\n`;
            
            for (let y = 0; y < pattern.height; y++) {
                for (let x = 0; x < pattern.width; x++) {
                    const color = pattern.data[y][x];
                    if (color !== '#000000') {
                        const rgb = this.hexToRgb(color);
                        customFunctions += `  leds[XY(${x}, ${y})] = CRGB(${rgb.r}, ${rgb.g}, ${rgb.b});\n`;
                    }
                }
            }
            
            customFunctions += `}\n`;
        });
        
        // Add the custom functions before the last closing brace
        const lastBraceIndex = enhancedCode.lastIndexOf('}');
        if (lastBraceIndex !== -1) {
            enhancedCode = enhancedCode.slice(0, lastBraceIndex) + 
                          customFunctions + '\n' + 
                          enhancedCode.slice(lastBraceIndex);
        }
        
        return enhancedCode;
    }
    
    previewArduinoCode() {
        if (!this.arduinoPackage) {
            this.generateArduinoPackage();
            return;
        }
        
        document.getElementById('arduino-code-display').textContent = this.arduinoPackage.code;
        document.getElementById('arduino-preview').style.display = 'block';
        document.getElementById('arduino-preview').scrollIntoView({ behavior: 'smooth' });
    }
    
    copyArduinoCode() {
        if (!this.arduinoPackage) {
            this.log('Generate Arduino package first', 'warning');
            return;
        }
        
        navigator.clipboard.writeText(this.arduinoPackage.code).then(() => {
            this.log('Arduino code copied to clipboard', 'success');
        }).catch(() => {
            this.log('Failed to copy code to clipboard', 'error');
        });
    }
    
    downloadArduinoFile() {
        if (!this.arduinoPackage) {
            this.log('Generate Arduino package first', 'warning');
            return;
        }
        
        const blob = new Blob([this.arduinoPackage.code], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `led_matrix_${this.arduinoPackage.config.width}x${this.arduinoPackage.config.height}.ino`;
        a.click();
        URL.revokeObjectURL(url);
        
        this.log('Arduino file downloaded', 'success');
    }
    
    async downloadArduinoPackage() {
        if (!this.arduinoPackage) {
            this.log('Generate Arduino package first', 'warning');
            return;
        }
        
        this.log('Preparing Arduino package download...', 'warning');
        
        try {
            // Create ZIP file using JSZip (we'll need to include this library)
            const zip = new JSZip();
            
            // Main Arduino file
            const filename = `led_matrix_${this.arduinoPackage.config.width}x${this.arduinoPackage.config.height}`;
            zip.file(`${filename}.ino`, this.arduinoPackage.code);
            
            // README file
            if (this.arduinoPackage.includeReadme) {
                const readme = this.generateReadmeFile();
                zip.file('README.md', readme);
            }
            
            // Wiring diagram
            if (this.arduinoPackage.wiring) {
                const wiringGuide = this.generateWiringMarkdown(this.arduinoPackage.wiring);
                zip.file('WIRING.md', wiringGuide);
            } else if (this.arduinoPackage.includeWiring) {
                // Generate wiring data for the Arduino package
                const wiringData = await this.generateWiringForArduino();
                if (wiringData) {
                    const wiringGuide = this.generateWiringMarkdown(wiringData);
                    zip.file('WIRING.md', wiringGuide);
                }
            }
            
            // Pattern files
            if (this.arduinoPackage.patterns.length > 0) {
                const patternsFolder = zip.folder('patterns');
                this.arduinoPackage.patterns.forEach((pattern, index) => {
                    patternsFolder.file(`${pattern.name.replace(/[^a-zA-Z0-9]/g, '_')}.json`, JSON.stringify(pattern, null, 2));
                });
            }
            
            // Library information
            if (this.arduinoPackage.includeLibraries) {
                const libraryInfo = this.generateLibraryInfo();
                zip.file('LIBRARIES.md', libraryInfo);
            }
            
            // Generate and download ZIP
            const content = await zip.generateAsync({ type: 'blob' });
            const url = URL.createObjectURL(content);
            const a = document.createElement('a');
            a.href = url;
            a.download = `${filename}_package.zip`;
            a.click();
            URL.revokeObjectURL(url);
            
            this.log('Arduino package downloaded successfully', 'success');
            
        } catch (error) {
            this.log(`Error creating package: ${error.message}`, 'error');
        }
    }
    
    generateReadmeFile() {
        const config = this.arduinoPackage.config;
        const board = this.arduinoPackage.board;
        
        return `# LED Matrix Project

## Overview
This Arduino project controls a ${config.width}×${config.height} LED matrix using FastLED library.

## Hardware Requirements
- ${board.replace('_', ' ').toUpperCase()} board
- WS2812B LED strip (${config.width * config.height} LEDs)
- 5V Power Supply (see WIRING.md for power requirements)
- Jumper wires and breadboard
- 1000µF capacitor
- 330Ω resistor
${board.includes('esp') ? '- 74HCT125 level shifter' : ''}

## Software Requirements
- Arduino IDE
- FastLED library (install via Library Manager)

## Installation
1. Open Arduino IDE
2. Install FastLED library: Tools → Manage Libraries → Search "FastLED"
3. Open the .ino file
4. Select your board: Tools → Board → ${board.replace('_', ' ')}
5. Select correct COM port: Tools → Port
6. Upload the code

## Configuration
- Matrix Size: ${config.width}×${config.height}
- Data Pin: ${config.dataPin}
- Brightness: ${config.brightness}/255
- Total LEDs: ${config.width * config.height}

## Patterns Included
- Solid Colors
- Rainbow
- Plasma Effect
- Fire Simulation
- Matrix Rain
- Twinkle
${this.arduinoPackage.patterns.length > 0 ? `- ${this.arduinoPackage.patterns.length} Custom Patterns` : ''}

## Usage
The matrix will automatically cycle through patterns every 10 seconds. You can modify the pattern duration by changing the PATTERN_DURATION constant.

## Troubleshooting
- If LEDs don't light up, check power connections
- If colors are wrong, verify COLOR_ORDER setting
- If patterns are corrupted, check data pin connection
- Monitor Serial output for debugging information

## Customization
You can modify patterns by editing the pattern functions or add new ones following the existing examples.

Generated by LED Matrix Control Center
`;
    }
    
    generateLibraryInfo() {
        return `# Required Libraries

## FastLED
**Version:** Latest (3.5.0 or newer recommended)
**Installation:** Arduino IDE → Tools → Manage Libraries → Search "FastLED"
**Purpose:** Controls WS2812B LED strips with optimized performance

### Alternative Installation Methods:
1. **Library Manager (Recommended):**
   - Open Arduino IDE
   - Go to Tools → Manage Libraries
   - Search for "FastLED"
   - Click Install

2. **Manual Installation:**
   - Download from: https://github.com/FastLED/FastLED
   - Extract to Arduino/libraries/ folder
   - Restart Arduino IDE

3. **PlatformIO:**
   \`\`\`
   lib_deps = fastled/FastLED@^3.5.0
   \`\`\`

## Documentation
- FastLED Documentation: https://fastled.io/
- WS2812B Datasheet: Available from LED strip manufacturer
- Arduino Reference: https://www.arduino.cc/reference/

## Compatibility
- Arduino Uno/Nano: Native 5V, no level shifter needed
- ESP32/ESP8266: 3.3V logic, level shifter recommended for reliable operation

Generated by LED Matrix Control Center
`;
    }
    
    updatePackageContents() {
        const container = document.getElementById('package-contents');
        if (!this.arduinoPackage) {
            container.innerHTML = '<p>Generate a package to see contents...</p>';
            return;
        }
        
        const config = this.arduinoPackage.config;
        const filename = `led_matrix_${config.width}x${config.height}`;
        
        let html = '<div class="package-file-list">';
        
        // Main Arduino file
        html += `
            <div class="package-file">
                <span class="file-icon">📄</span>
                <div>
                    <div class="file-name">${filename}.ino</div>
                    <div class="file-description">Main Arduino sketch with all patterns and configuration</div>
                </div>
            </div>
        `;
        
        // README
        if (this.arduinoPackage.includeReadme) {
            html += `
                <div class="package-file">
                    <span class="file-icon">📖</span>
                    <div>
                        <div class="file-name">README.md</div>
                        <div class="file-description">Complete setup and usage instructions</div>
                    </div>
                </div>
            `;
        }
        
        // Wiring diagram
        if (this.arduinoPackage.wiring) {
            html += `
                <div class="package-file">
                    <span class="file-icon">🔌</span>
                    <div>
                        <div class="file-name">WIRING.md</div>
                        <div class="file-description">Wiring diagram and power calculations</div>
                    </div>
                </div>
            `;
        }
        
        // Library info
        if (this.arduinoPackage.includeLibraries) {
            html += `
                <div class="package-file">
                    <span class="file-icon">📚</span>
                    <div>
                        <div class="file-name">LIBRARIES.md</div>
                        <div class="file-description">Required libraries and installation instructions</div>
                    </div>
                </div>
            `;
        }
        
        // Pattern files
        if (this.arduinoPackage.patterns.length > 0) {
            html += `
                <div class="package-file">
                    <span class="file-icon">📁</span>
                    <div>
                        <div class="file-name">patterns/ (${this.arduinoPackage.patterns.length} files)</div>
                        <div class="file-description">Custom pattern data files for backup and sharing</div>
                    </div>
                </div>
            `;
        }
        
        html += '</div>';
        
        // Package summary
        html += `
            <div class="package-summary">
                <h4>Package Summary</h4>
                <ul>
                    <li><strong>Board:</strong> ${this.arduinoPackage.board.replace('_', ' ').toUpperCase()}</li>
                    <li><strong>Matrix Size:</strong> ${config.width}×${config.height} (${config.width * config.height} LEDs)</li>
                    <li><strong>Data Pin:</strong> ${config.dataPin}</li>
                    <li><strong>Brightness:</strong> ${config.brightness}/255</li>
                    <li><strong>Custom Patterns:</strong> ${this.arduinoPackage.patterns.length}</li>
                    <li><strong>Ready to Upload:</strong> Yes</li>
                </ul>
            </div>
        `;
        
        container.innerHTML = html;
    }
    
    async generateWiringForArduino() {
        try {
            const config = this.arduinoPackage.config;
            const board = this.arduinoPackage.board;
            
            const response = await fetch(`${this.apiBase}/wiring`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    controller: board,
                    width: config.width,
                    height: config.height,
                    ledsPerMeter: 144,
                    powerSupply: '5V10A'
                })
            });
            
            if (response.ok) {
                const data = await response.json();
                return data.wiring;
            }
        } catch (error) {
            console.error('Error generating wiring data:', error);
        }
        return null;
    }
    
    syncArduinoSettings() {
        // Sync Arduino settings with current matrix configuration
        document.getElementById('arduino-width').value = this.matrixSize.width;
        document.getElementById('arduino-height').value = this.matrixSize.height;
        
        // Update data pin based on board selection
        const board = document.getElementById('arduino-board').value;
        const defaultPins = {
            arduino_uno: 6,
            arduino_nano: 6,
            esp32: 13,
            esp8266: 2
        };
        
        if (defaultPins[board]) {
            document.getElementById('arduino-data-pin').value = defaultPins[board];
        }
    }
    
    // Add API endpoint for custom pattern data
    async sendCustomPattern(patternData) {
        try {
            const response = await fetch(`${this.apiBase}/pattern`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    type: 'custom',
                    data: patternData,
                    brightness: this.brightness,
                    speed: this.speed
                })
            });
            
            if (response.ok) {
                return await response.json();
            } else {
                throw new Error('Failed to send custom pattern');
            }
        } catch (error) {
            console.error('Error sending custom pattern:', error);
            throw error;
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