function initializePaletteSection() {
    console.log('Initializing palette section');
    loadPalettes();
    setupPaletteEventListeners();
    setupPaletteColorPicker();
}

function setupPaletteEventListeners() {
    document.getElementById('save-palette').addEventListener('click', () => {
        const name = document.getElementById('palette-name').value;
        const colors = getCurrentPalette();
        if (name && colors.length > 0) {
            savePalette(name, colors);
        } else {
            alert('Please enter a name and add some colors to your palette.');
        }
    });

    document.getElementById('load-palette').addEventListener('click', () => {
        const selectedPalette = document.querySelector('#saved-palettes li.selected');
        if (selectedPalette) {
            const paletteName = selectedPalette.textContent;
            loadPalette(paletteName);
        } else {
            alert('Please select a palette to load.');
        }
    });

    document.getElementById('delete-palette').addEventListener('click', () => {
        const selectedPalette = document.querySelector('#saved-palettes li.selected');
        if (selectedPalette) {
            const paletteName = selectedPalette.textContent;
            if (confirm(`Are you sure you want to delete the palette "${paletteName}"?`)) {
                deletePalette(paletteName);
            }
        } else {
            alert('Please select a palette to delete.');
        }
    });
}

function setupPaletteColorPicker() {
    const colorPicker = document.getElementById('palette-color-picker');
    const addColorBtn = document.getElementById('add-color-to-palette');
    const paletteGrid = document.querySelector('.palette-grid');

    addColorBtn.addEventListener('click', () => {
        const color = colorPicker.value;
        const colorDiv = document.createElement('div');
        colorDiv.className = 'palette-color';
        colorDiv.style.backgroundColor = color;
        colorDiv.addEventListener('click', () => {
            paletteGrid.removeChild(colorDiv);
        });
        paletteGrid.appendChild(colorDiv);
    });
}

function getCurrentPalette() {
    const colors = [];
    const paletteGrid = document.querySelector('.palette-grid');
    paletteGrid.querySelectorAll('.palette-color').forEach(colorDiv => {
        colors.push(colorDiv.style.backgroundColor);
    });
    return colors;
}

async function savePalette(name, colors) {
    try {
        const response = await fetch('/api/palettes', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, colors })
        });
        if (response.ok) {
            loadPalettes();
            log(`Palette "${name}" saved`, 'success');
        } else {
            throw new Error('Failed to save palette');
        }
    } catch (error) {
        log(`Error saving palette: ${error.message}`, 'error');
    }
}

async function loadPalette(name) {
    try {
        const response = await fetch('/api/palettes');
        if (response.ok) {
            const palettes = await response.json();
            const colors = palettes[name];
            if (colors) {
                const paletteGrid = document.querySelector('.palette-grid');
                paletteGrid.innerHTML = '';
                colors.forEach(color => {
                    const colorDiv = document.createElement('div');
                    colorDiv.className = 'palette-color';
                    colorDiv.style.backgroundColor = color;
                    colorDiv.addEventListener('click', () => {
                        paletteGrid.removeChild(colorDiv);
                    });
                    paletteGrid.appendChild(colorDiv);
                });
            }
        } else {
            throw new Error('Failed to load palettes');
        }
    } catch (error) {
        log(`Error loading palette: ${error.message}`, 'error');
    }
}

async function loadPalettes() {
    try {
        const response = await fetch('/api/palettes');
        if (response.ok) {
            const palettes = await response.json();
            const savedPalettes = document.getElementById('saved-palettes');
            savedPalettes.innerHTML = '';
            for (const name in palettes) {
                const li = document.createElement('li');
                li.textContent = name;
                li.addEventListener('click', () => {
                    document.querySelectorAll('#saved-palettes li').forEach(item => {
                        item.classList.remove('selected');
                    });
                    li.classList.add('selected');
                });
                savedPalettes.appendChild(li);
            }
        } else {
            throw new Error('Failed to load palettes');
        }
    } catch (error) {
        log(`Error loading palettes: ${error.message}`, 'error');
    }
}

async function deletePalette(name) {
    try {
        const response = await fetch(`/api/palettes/${name}`, {
            method: 'DELETE'
        });
        if (response.ok) {
            loadPalettes();
            log(`Palette "${name}" deleted`, 'success');
        } else {
            throw new Error('Failed to delete palette');
        }
    } catch (error) {
        log(`Error deleting palette: ${error.message}`, 'error');
    }
}
