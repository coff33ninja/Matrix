// LED Matrix Control Center - Main Application
class MatrixController {
    constructor() {
        // Always use absolute path for API regardless of base tag
        this.apiBase = '/api';
        this.connected = false;
        this.matrixSize = { width: 16, height: 16 };
        this.currentPattern = 'solid';
        this.fps = 0;
        
        // Initialize drawing variables
        this.drawingMode = 'paint';
        this.brushColor = '#e94560';
        this.brushSize = 1;
        this.isDrawing = false;
        this.drawingData = [];
        this.savedPatterns = JSON.parse(localStorage.getItem('ledMatrixPatterns') || '[]');
        
        this.init();
    }

    async init() {
        this.setupEventListeners();
        await this.checkConnection();
        this.startStatusUpdates();
        this.log('System initialized', 'success');
        this.switchSection('control');
    }

    setupEventListeners() {
        // Navigation tabs
        document.querySelectorAll('.nav-tab').forEach(tab => {
            tab.addEventListener('click', (e) => {
                e.preventDefault();
                this.switchSection(tab.dataset.section);
            });
        });
    }

    async switchSection(sectionName) {
        // Update active tab
        document.querySelectorAll('.nav-tab').forEach(tab => tab.classList.remove('active'));
        document.querySelector(`[data-section="${sectionName}"]`).classList.add('active');

        // Load section content
        const response = await fetch(`sections/${sectionName}.html`);
        const html = await response.text();
        document.querySelector('.content-section').innerHTML = html;

        // Load section-specific data and setup event listeners
        this.loadSectionData(sectionName);
    }

    async loadSectionData(section) {
        switch(section) {
            case 'control':
                initializeControlSection();
                setupControlEventListeners();
                break;
            case 'generator':
                initializeGeneratorSection();
                setupGeneratorEventListeners();
                break;
            case 'wiring':
                initializeWiringSection();
                setupWiringEventListeners();
                break;
            case 'arduino':
                initializeArduinoSection();
                setupArduinoEventListeners();
                break;
            case 'config':
                await initializeConfigSection();
                setupConfigEventListeners();
                break;
            case 'monitor':
                await initializeMonitorSection();
                setupMonitorEventListeners();
                break;
            case 'palette':
                initializePaletteSection();
                break;
            case 'custom-matrix':
                initializeCustomMatrixSection();
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

    calculateEstimatedCost(totalLeds, stripLength, maxPower) {
        const controller = document.getElementById('wiring-controller')?.value || 'arduino_uno';
        const controllerCost = getControllerPrice(controller);
        const stripCost = Math.ceil(stripLength) * 12; // $12 per meter
        const psuCost = this.getPSUCost(maxPower);
        const accessoriesCost = 15; // Level shifter, wires, etc.
        
        const total = controllerCost + stripCost + psuCost + accessoriesCost;
        return `$${total - 10}-${total + 10}`;
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
        const controllerName = getControllerName(controller);
        const controllerPrice = getControllerPrice(controller);
        const stripPrice = Math.ceil(stripLength) * 12;
        const psuPrice = this.getPSUCost(maxPower);
        const recommendedPSU = getRecommendedPSU(maxPower);
        
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

    // Mermaid diagram generation
    generateMermaidDiagram() {
        const controller = document.getElementById('wiring-controller')?.value || 'arduino_uno';
        const controllerName = getControllerName(controller);
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
            case 'fire':
                this.animateFire(pixels);
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

    animateFire(pixels) {
        const fire = new Array(this.matrixSize.width * this.matrixSize.height).fill(0);
        const animate = () => {
            for (let i = 0; i < this.matrixSize.width; i++) {
                fire[i + this.matrixSize.width * (this.matrixSize.height - 1)] = Math.random() * 255;
            }
            for (let y = 0; y < this.matrixSize.height - 1; y++) {
                for (let x = 0; x < this.matrixSize.width; x++) {
                    const src = y * this.matrixSize.width + x;
                    const dest = ((y + 1) % this.matrixSize.height) * this.matrixSize.width + (x % this.matrixSize.width);
                    const rand = Math.floor(Math.random() * 2);
                    fire[src] = ((fire[dest] + fire[(dest + 1) % fire.length] + fire[(dest + 2) % fire.length]) / 3.5) * 1.05 - rand;
                    if (fire[src] > 255) fire[src] = 255;
                    if (fire[src] < 0) fire[src] = 0;
                    const c = fire[src];
                    let r, g, b;
                    if (c < 85) {
                        r = c * 3;
                        g = 0;
                        b = 0;
                    } else if (c < 170) {
                        r = 255;
                        g = (c - 85) * 3;
                        b = 0;
                    } else {
                        r = 255;
                        g = 255;
                        b = (c - 170) * 3;
                    }
                    pixels[src].style.backgroundColor = `rgb(${r},${g},${b})`;
                }
            }
            requestAnimationFrame(animate);
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

    setupMatrixDrawing() {
        const pixels = document.querySelectorAll('.led-pixel');
        console.log('Setting up drawing for', pixels.length, 'pixels');
        
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
        console.log('Drawing pixel:', index, 'Mode:', this.drawingMode, 'Color:', this.brushColor);
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
        } else if (this.drawingMode === 'line') {
            if (!this.lineStart) {
                this.lineStart = { x, y };
            } else {
                this.drawLine(this.lineStart.x, this.lineStart.y, x, y);
                this.lineStart = null;
            }
        }
    }

    drawLine(x0, y0, x1, y1) {
        const dx = Math.abs(x1 - x0);
        const dy = Math.abs(y1 - y0);
        const sx = (x0 < x1) ? 1 : -1;
        const sy = (y0 < y1) ? 1 : -1;
        let err = dx - dy;

        while (true) {
            this.paintPixels(x0, y0);
            if ((x0 === x1) && (y0 === y1)) break;
            const e2 = 2 * err;
            if (e2 > -dy) {
                err -= dy;
                x0 += sx;
            }
            if (e2 < dx) {
                err += dx;
                y0 += sy;
            }
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
                        this.applySavedPattern(pattern);
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
    
    applySavedPattern(pattern) {
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
            this.applySavedPattern(patterns[patternName]);
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
                this.applySavedPattern(pattern);
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
                const rgb = hexToRgb(color);
                row.push([rgb.r, rgb.g, rgb.b]);
            }
            matrixData.push(row);
        }
        
        return matrixData;
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
        log(message, type);
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.matrixController = new MatrixController();
});