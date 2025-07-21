// Mermaid Configuration for LED Matrix Documentation
// Custom theme and interactive features

const mermaidConfig = {
    theme: 'dark',
    themeVariables: {
        // Primary colors matching our design
        primaryColor: '#1a1a2e',
        primaryTextColor: '#f1f1f1',
        primaryBorderColor: '#e94560',
        lineColor: '#e94560',
        
        // Secondary colors
        secondaryColor: '#16213e',
        tertiaryColor: '#0f3460',
        
        // Node colors for different components
        cScale0: '#1a1a2e',  // Controllers
        cScale1: '#16213e',  // Power supplies
        cScale2: '#0f3460',  // LED matrices
        cScale3: '#e94560',  // Data connections
        
        // Text and labels
        labelTextColor: '#f1f1f1',
        edgeLabelBackground: 'rgba(26, 26, 46, 0.9)',
        
        // Flowchart specific
        clusterBkg: 'rgba(15, 52, 96, 0.3)',
        clusterBorder: '#e94560',
        
        // Git graph colors
        git0: '#e94560',
        git1: '#4ade80',
        git2: '#fbbf24',
        git3: '#8b5cf6',
        
        // Pie chart colors
        pie1: '#e94560',
        pie2: '#4ade80',
        pie3: '#fbbf24',
        pie4: '#8b5cf6',
        pie5: '#06b6d4',
        
        // Gantt chart
        gridColor: 'rgba(233, 69, 96, 0.3)',
        section0: '#1a1a2e',
        section1: '#16213e',
        section2: '#0f3460',
        
        // State diagram
        fillType0: '#1a1a2e',
        fillType1: '#16213e',
        fillType2: '#0f3460'
    },
    
    // Flowchart configuration
    flowchart: {
        useMaxWidth: true,
        htmlLabels: true,
        curve: 'basis',
        padding: 20,
        nodeSpacing: 50,
        rankSpacing: 50,
        diagramPadding: 20
    },
    
    // Sequence diagram configuration
    sequence: {
        useMaxWidth: true,
        diagramMarginX: 50,
        diagramMarginY: 10,
        actorMargin: 50,
        width: 150,
        height: 65,
        boxMargin: 10,
        boxTextMargin: 5,
        noteMargin: 10,
        messageMargin: 35,
        mirrorActors: true,
        bottomMarginAdj: 1,
        rightAngles: false,
        showSequenceNumbers: false
    },
    
    // Gantt configuration
    gantt: {
        useMaxWidth: true,
        leftPadding: 75,
        gridLineStartPadding: 35,
        fontSize: 11,
        sectionFontSize: 24,
        numberSectionStyles: 4
    },
    
    // Git graph configuration
    gitGraph: {
        useMaxWidth: true,
        mainBranchName: 'main',
        showBranches: true,
        showCommitLabel: true,
        rotateCommitLabel: true
    },
    
    // Security level
    securityLevel: 'loose',
    
    // Start on load
    startOnLoad: true,
    
    // Log level
    logLevel: 'error',
    
    // Font family
    fontFamily: '"Segoe UI", Tahoma, Geneva, Verdana, sans-serif'
};

// Initialize Mermaid with custom config
if (typeof mermaid !== 'undefined') {
    mermaid.initialize(mermaidConfig);
}

// Interactive diagram features
class MermaidInteractive {
    constructor() {
        this.zoomLevel = 1;
        this.panX = 0;
        this.panY = 0;
        this.isDragging = false;
        this.lastMouseX = 0;
        this.lastMouseY = 0;
        
        this.initializeInteractivity();
    }
    
    initializeInteractivity() {
        // Wait for DOM to be ready
        document.addEventListener('DOMContentLoaded', () => {
            this.setupDiagramControls();
            this.setupZoomAndPan();
            this.setupDiagramGeneration();
        });
    }
    
    setupDiagramControls() {
        // Add control buttons to each mermaid container
        document.querySelectorAll('.mermaid-container').forEach(container => {
            const controls = document.createElement('div');
            controls.className = 'mermaid-controls';
            controls.innerHTML = `
                <button class="mermaid-control-btn" onclick="mermaidInteractive.zoomIn(this)" title="Zoom In">
                    <i class="fas fa-search-plus"></i>
                </button>
                <button class="mermaid-control-btn" onclick="mermaidInteractive.zoomOut(this)" title="Zoom Out">
                    <i class="fas fa-search-minus"></i>
                </button>
                <button class="mermaid-control-btn" onclick="mermaidInteractive.resetZoom(this)" title="Reset View">
                    <i class="fas fa-expand-arrows-alt"></i>
                </button>
                <button class="mermaid-control-btn" onclick="mermaidInteractive.downloadSVG(this)" title="Download SVG">
                    <i class="fas fa-file-code"></i>
                </button>
                <button class="mermaid-control-btn" onclick="mermaidInteractive.downloadPNG(this)" title="Download PNG">
                    <i class="fas fa-download"></i>
                </button>
            `;
            container.appendChild(controls);
        });
    }
    
    setupZoomAndPan() {
        document.querySelectorAll('.mermaid').forEach(diagram => {
            // Mouse wheel zoom
            diagram.addEventListener('wheel', (e) => {
                e.preventDefault();
                const delta = e.deltaY > 0 ? 0.9 : 1.1;
                this.zoom(diagram, delta);
            });
            
            // Mouse drag pan
            diagram.addEventListener('mousedown', (e) => {
                this.isDragging = true;
                this.lastMouseX = e.clientX;
                this.lastMouseY = e.clientY;
                diagram.style.cursor = 'grabbing';
            });
            
            diagram.addEventListener('mousemove', (e) => {
                if (this.isDragging) {
                    const deltaX = e.clientX - this.lastMouseX;
                    const deltaY = e.clientY - this.lastMouseY;
                    this.pan(diagram, deltaX, deltaY);
                    this.lastMouseX = e.clientX;
                    this.lastMouseY = e.clientY;
                }
            });
            
            diagram.addEventListener('mouseup', () => {
                this.isDragging = false;
                diagram.style.cursor = 'grab';
            });
            
            diagram.addEventListener('mouseleave', () => {
                this.isDragging = false;
                diagram.style.cursor = 'grab';
            });
        });
    }
    
    setupDiagramGeneration() {
        // Add dynamic diagram generation capabilities
        window.generateWiringDiagram = (controller, width, height) => {
            this.generateWiringDiagram(controller, width, height);
        };
    }
    
    zoomIn(button) {
        const container = button.closest('.mermaid-container');
        const diagram = container.querySelector('.mermaid');
        this.zoom(diagram, 1.2);
    }
    
    zoomOut(button) {
        const container = button.closest('.mermaid-container');
        const diagram = container.querySelector('.mermaid');
        this.zoom(diagram, 0.8);
    }
    
    resetZoom(button) {
        const container = button.closest('.mermaid-container');
        const diagram = container.querySelector('.mermaid');
        diagram.style.transform = 'scale(1) translate(0, 0)';
        this.zoomLevel = 1;
        this.panX = 0;
        this.panY = 0;
    }
    
    zoom(diagram, factor) {
        this.zoomLevel *= factor;
        this.zoomLevel = Math.max(0.1, Math.min(3, this.zoomLevel));
        this.updateTransform(diagram);
    }
    
    pan(diagram, deltaX, deltaY) {
        this.panX += deltaX;
        this.panY += deltaY;
        this.updateTransform(diagram);
    }
    
    updateTransform(diagram) {
        diagram.style.transform = `scale(${this.zoomLevel}) translate(${this.panX}px, ${this.panY}px)`;
    }
    
    downloadSVG(button) {
        const container = button.closest('.mermaid-container');
        const svg = container.querySelector('svg');
        if (svg) {
            const svgData = new XMLSerializer().serializeToString(svg);
            const blob = new Blob([svgData], { type: 'image/svg+xml' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'wiring-diagram.svg';
            a.click();
            URL.revokeObjectURL(url);
        }
    }
    
    downloadPNG(button) {
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
                    a.download = 'wiring-diagram.png';
                    a.click();
                    URL.revokeObjectURL(pngUrl);
                }, 'image/png');
                
                URL.revokeObjectURL(url);
            };
            
            img.src = url;
        }
    }
    
    async generateWiringDiagram(controller, width, height) {
        try {
            // Call the Python API to generate wiring diagram
            const response = await fetch('http://localhost:8080/wiring', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ controller, width, height })
            });
            
            if (response.ok) {
                const data = await response.json();
                // Extract Mermaid diagram from the guide
                const mermaidMatch = data.guide.match(/```mermaid\n([\s\S]*?)\n```/);
                if (mermaidMatch) {
                    const diagramCode = mermaidMatch[1];
                    this.renderDynamicDiagram(diagramCode);
                }
            }
        } catch (error) {
            console.error('Error generating wiring diagram:', error);
        }
    }
    
    renderDynamicDiagram(diagramCode) {
        // Create a new container for the dynamic diagram
        const container = document.createElement('div');
        container.className = 'mermaid-container dynamic-diagram';
        container.innerHTML = `
            <h4>Generated Wiring Diagram</h4>
            <div class="mermaid">${diagramCode}</div>
        `;
        
        // Add to the page
        const targetSection = document.getElementById('wiring');
        if (targetSection) {
            targetSection.appendChild(container);
            
            // Re-initialize Mermaid for the new diagram
            mermaid.init(undefined, container.querySelector('.mermaid'));
            
            // Add controls to the new diagram
            this.setupDiagramControls();
        }
    }
}

// Initialize interactive features
const mermaidInteractive = new MermaidInteractive();

// Export for global access
window.mermaidInteractive = mermaidInteractive;
window.mermaidConfig = mermaidConfig;