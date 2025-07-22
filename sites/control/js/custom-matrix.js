function initializeCustomMatrixSection() {
    console.log('Initializing custom matrix section');
    setupCustomMatrixEventListeners();
}

function setupCustomMatrixEventListeners() {
    document.getElementById('create-custom-matrix').addEventListener('click', () => {
        const width = document.getElementById('custom-matrix-width').value;
        const height = document.getElementById('custom-matrix-height').value;
        createCustomMatrix(width, height);
    });

    document.getElementById('import-image').addEventListener('click', () => {
        const fileInput = document.getElementById('image-importer');
        const file = fileInput.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = (e) => {
                const img = new Image();
                img.onload = () => {
                    const canvas = document.createElement('canvas');
                    const ctx = canvas.getContext('2d');
                    const width = document.getElementById('custom-matrix-width').value;
                    const height = document.getElementById('custom-matrix-height').value;
                    canvas.width = width;
                    canvas.height = height;
                    ctx.drawImage(img, 0, 0, width, height);
                    const imageData = ctx.getImageData(0, 0, width, height);
                    const matrixData = [];
                    for (let i = 0; i < imageData.data.length; i += 4) {
                        const r = imageData.data[i];
                        const g = imageData.data[i + 1];
                        const b = imageData.data[i + 2];
                        matrixData.push([r, g, b]);
                    }
                    displayMatrix(matrixData, width, height);
                };
                img.src = e.target.result;
            };
            reader.readAsDataURL(file);
        }
    });

    document.getElementById('send-custom-matrix').addEventListener('click', () => {
        const matrixData = getMatrixData();
        sendMatrixData(matrixData);
    });
}

function createCustomMatrix(width, height) {
    const grid = document.getElementById('custom-matrix-grid');
    grid.innerHTML = '';
    grid.style.gridTemplateColumns = `repeat(${width}, 1fr)`;
    for (let i = 0; i < width * height; i++) {
        const pixel = document.createElement('div');
        pixel.className = 'led-pixel';
        pixel.addEventListener('click', () => {
            pixel.style.backgroundColor = document.getElementById('brush-color').value;
        });
        grid.appendChild(pixel);
    }
    window.matrixController.matrixSize = { width, height };
    window.matrixController.updatePowerCalculations();
}

function displayMatrix(matrixData, width, height) {
    const grid = document.getElementById('custom-matrix-grid');
    grid.innerHTML = '';
    grid.style.gridTemplateColumns = `repeat(${width}, 1fr)`;
    for (let i = 0; i < matrixData.length; i++) {
        const pixel = document.createElement('div');
        pixel.className = 'led-pixel';
        const rgb = matrixData[i];
        pixel.style.backgroundColor = `rgb(${rgb[0]}, ${rgb[1]}, ${rgb[2]})`;
        grid.appendChild(pixel);
    }
}

function getMatrixData() {
    const grid = document.getElementById('custom-matrix-grid');
    const pixels = grid.querySelectorAll('.led-pixel');
    const matrixData = [];
    pixels.forEach(pixel => {
        const rgb = pixel.style.backgroundColor.match(/\d+/g).map(Number);
        matrixData.push(rgb);
    });
    return matrixData;
}

async function sendMatrixData(matrixData) {
    try {
        const response = await fetch('/api/pattern', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                pattern: 'custom',
                data: matrixData
            })
        });
        if (response.ok) {
            log('Matrix data sent successfully', 'success');
        } else {
            throw new Error('Failed to send matrix data');
        }
    } catch (error) {
        log(`Error sending matrix data: ${error.message}`, 'error');
    }
}
