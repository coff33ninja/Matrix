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
                this.wiringGuide = data.guide;
                
                // Update power calculations
                this.updatePowerCalculations(data);
                
                // Generate Mermaid diagram
                this.generateMermaidDiagram(data);
                
                // Update component list
                this.updateComponentList(data);
            } else {
                throw new Error('Failed to generate wiring guide');
            }
        } catch (error) {
            this.log(`Error generating wiring: ${error.message}`, 'error');
        }
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