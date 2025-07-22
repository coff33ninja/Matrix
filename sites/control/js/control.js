// sites/control/js/control.js

function setupControlEventListeners() {
    // Control section
    document.getElementById('apply-pattern').addEventListener('click', () => window.matrixController.applyPattern());
    document.getElementById('clear-matrix').addEventListener('click', () => window.matrixController.clearMatrix());
    document.getElementById('test-pattern').addEventListener('click', () => window.matrixController.testPattern());

    // Sliders
    document.getElementById('brightness-slider').addEventListener('input', (e) => {
        document.getElementById('brightness-value').textContent = e.target.value;
    });

    document.getElementById('speed-slider').addEventListener('input', (e) => {
        document.getElementById('speed-value').textContent = e.target.value;
    });

    // Drawing section event listeners
    setupDrawingEventListeners();
}

function setupDrawingEventListeners() {
    // Drawing mode and tools
    document.getElementById('drawing-mode').addEventListener('change', (e) => {
        window.matrixController.drawingMode = e.target.value;
        window.matrixController.updateDrawingCursor();
    });

    document.getElementById('brush-color').addEventListener('change', (e) => {
        window.matrixController.brushColor = e.target.value;
    });

    document.getElementById('brush-size').addEventListener('input', (e) => {
        window.matrixController.brushSize = parseInt(e.target.value);
        document.getElementById('brush-size-display').textContent = `${window.matrixController.brushSize}x${window.matrixController.brushSize}`;
    });

    // Color presets
    document.querySelectorAll('.color-preset').forEach(preset => {
        preset.addEventListener('click', (e) => {
            const color = e.target.dataset.color;
            window.matrixController.brushColor = color;
            document.getElementById('brush-color').value = color;

            // Update active preset
            document.querySelectorAll('.color-preset').forEach(p => p.classList.remove('active'));
            e.target.classList.add('active');
        });
    });

    // Drawing actions
    document.getElementById('clear-drawing').addEventListener('click', () => window.matrixController.clearDrawing());
    document.getElementById('send-to-matrix').addEventListener('click', () => window.matrixController.sendDrawingToMatrix());

    // Quick Patterns
    document.querySelectorAll('.pattern-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const pattern = e.currentTarget.dataset.pattern;
            window.matrixController.loadPresetPattern(pattern);
        });
    });

    document.getElementById('save-pattern').addEventListener('click', () => window.matrixController.savePattern());
    document.getElementById('load-pattern').addEventListener('click', () => window.matrixController.loadPattern());
}

function initializeControlSection() {
    window.matrixController.initializeMatrix();
    // Wait a bit for DOM to be ready, then setup drawing
    setTimeout(() => {
        window.matrixController.initializeDrawingData();
        window.matrixController.setupMatrixDrawing();
    }, 100);
}
