# LED Matrix Project - Web Interfaces

Two-site architecture providing both real-time control and comprehensive documentation for your LED matrix project.

## 🏗️ Architecture Overview

```
sites/
├── control/          # Real-time Control Interface (Port 3000)
│   ├── index.html    # Modern control interface
│   ├── app.js        # Control functionality
│   └── README.md     # Control interface docs
├── docs/             # Comprehensive Documentation (Port 3001)
│   ├── index.html    # Complete project guide
│   └── README.md     # Documentation guide
└── README.md         # This overview
```

## 🚀 Quick Start Options

### Option 1: Start Everything
```bash
python matrix.py start
```
Starts GUI controller + control interface + documentation

### Option 2: Start Web Interfaces Only
```bash
# Both interfaces
python matrix.py web --type all

# Control interface only (port 3000)
python matrix.py web --type control

# Documentation only (port 3001)
python matrix.py web --type docs
```

### Option 3: Start Services Separately
```bash
# Terminal 1: Python controller
python matrix.py controller

# Terminal 2: Control interface
python matrix.py web --type control

# Terminal 3: Documentation
python matrix.py web --type docs
```

## 🌐 Access Points

- **🎮 Control Interface:** `http://localhost:3000`
- **📚 Documentation:** `http://localhost:3001`
- **🔌 API Server:** `http://localhost:8080`

## 🎮 Features

### Control Panel
- **Real-time pattern control** with live preview
- **Color picker** with brightness and speed controls
- **Pattern types**: Solid, Rainbow, Plasma, Fire, Matrix Rain
- **Matrix preview** showing current display state
- **Activity log** with timestamped events

### Arduino Code Generator
- **Multi-board support**: Uno, Nano, ESP32, ESP8266, Mega
- **Automatic code generation** based on matrix size
- **Board comparison** showing memory usage and suitability
- **One-click download** of generated Arduino code

### Wiring Diagram Generator
- **Interactive wiring guides** for different controllers
- **Power requirement calculations** with PSU recommendations
- **Component lists** with estimated costs
- **Downloadable guides** in Markdown format

### Configuration Management
- **Connection settings** (USB/WiFi, ports, baud rates)
- **Backup and restore** functionality
- **Real-time configuration updates**

### System Monitoring
- **Live system stats** (CPU, memory, uptime)
- **Hardware information** display
- **Performance metrics** tracking

## 🔧 API Endpoints

The web interface communicates with the Python controller via these endpoints:

### Status & Control
- `GET /status` - Get controller status and matrix info
- `POST /pattern` - Apply patterns with parameters
- `POST /clear` - Clear the matrix display

### Code Generation
- `POST /generate` - Generate Arduino code
- `POST /wiring` - Generate wiring diagrams

### Configuration
- `GET /config` - Get current configuration
- `POST /config` - Save configuration changes
- `POST /backup` - Create configuration backup
- `GET /backups` - List available backups

### System Info
- `GET /system` - Get system statistics
- `GET /hardware` - Get hardware information

## 🎨 Interface Sections

### 1. Control
- Pattern selection and customization
- Real-time matrix preview
- Color and brightness controls
- Activity logging

### 2. Generator
- Arduino code generation
- Board comparison and recommendations
- Matrix size configuration

### 3. Wiring
- Wiring diagram generation
- Power requirement calculations
- Component specifications

### 4. Config
- Connection settings
- Backup management
- Configuration persistence

### 5. Monitor
- System performance metrics
- Hardware status information
- Real-time monitoring

## 🔗 Integration with Python Modules

The web interface directly integrates with your existing Python modules:

- **`matrix_controller.py`** - Main controller and web API
- **`arduino_generator.py`** - Code generation functionality
- **`wiring_diagram_generator.py`** - Wiring guide creation
- **`matrix_config.py`** - Configuration management
- **`matrix_hardware.py`** - Hardware communication

## 🎯 Benefits Over Original HTML

### ✅ Improvements
- **Direct integration** with Python modules (no static content)
- **Real-time updates** and live preview
- **Modern, responsive design** that works on all devices
- **Functional API endpoints** that actually work
- **No external CDN dependencies** (production-ready)
- **Proper error handling** and user feedback
- **Organized sections** with clear navigation

### 🔧 Technical Improvements
- **CORS properly configured** for cross-origin requests
- **JSON API responses** instead of static content
- **Real-time status updates** every 2 seconds
- **Proper error handling** with user-friendly messages
- **Local asset serving** (no external dependencies)
- **Mobile-responsive design** for all screen sizes

## 🚀 Usage Examples

### Apply a Rainbow Pattern
```javascript
// Via web interface - just select "Rainbow" and click "Apply Pattern"
// Via API:
fetch('http://localhost:8080/pattern', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        pattern: 'rainbow',
        brightness: 200,
        speed: 75
    })
});
```

### Generate Arduino Code
```javascript
// Via web interface - configure board and matrix size, click "Generate"
// Via API:
fetch('http://localhost:8080/generate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        board: 'esp32',
        width: 16,
        height: 16
    })
});
```

## 🛠️ Development

### File Structure
```
sites/
├── index.html          # Main web interface
├── app.js             # JavaScript application logic
├── README.md          # This documentation
└── (served by serve_web.py)
```

### Customization
- **Colors**: Modify CSS variables in `index.html`
- **Features**: Add new sections and API endpoints
- **Patterns**: Extend pattern types in both JS and Python
- **Styling**: Update CSS for different themes

## 🔍 Troubleshooting

### Common Issues

1. **"Failed to connect to matrix controller"**
   - Ensure `python matrix.py controller` is running
   - Check that port 8080 is not blocked

2. **"CORS errors in browser console"**
   - Make sure you're accessing via `http://localhost:3000`
   - Don't open the HTML file directly in browser

3. **"Web interface not loading"**
   - Run `python serve_web.py` to start the web server
   - Check that port 3000 is available

4. **"API endpoints not working"**
   - Verify the Python controller is running with web server
   - Check browser developer tools for error messages

### Debug Mode
Enable debug logging by modifying the JavaScript console:
```javascript
window.matrixController.log('Debug message', 'info');
```

## 🎉 Next Steps

1. **Start both servers** (Python controller + web server)
2. **Open the web interface** in your browser
3. **Test the connection** using the status indicator
4. **Try different patterns** and see them in the preview
5. **Generate Arduino code** for your specific setup
6. **Create wiring diagrams** for your hardware configuration

The new web interface provides a much more integrated and functional experience compared to the original static HTML file, with real-time updates and direct integration with your Python modules.
## 🎮 Contr
ol Interface Features

- **Real-time LED control** with live matrix preview
- **Pattern generation** (Solid, Rainbow, Plasma, Fire, Matrix Rain)
- **Arduino code generator** with board comparison
- **Wiring diagram generator** with power calculations
- **Configuration management** with backup/restore
- **System monitoring** with live stats

## 📚 Documentation Features

- **Comprehensive project guide** with step-by-step instructions
- **Interactive Mermaid diagrams** for wiring and circuits
- **Component specifications** with shopping lists
- **Troubleshooting guides** with common solutions
- **Advanced features** and customization options
- **Mobile-responsive design** for all devices

## 🔗 Integration

- **Cross-linked navigation** between control and documentation
- **Unified design language** for consistent experience
- **API integration** with Python controller
- **Real-time updates** and live monitoring

## 📱 Mobile Support

Both interfaces are fully responsive and work on:
- Desktop computers and laptops
- Tablets (iPad, Android tablets)
- Mobile phones (iOS, Android)
- Any modern web browser

## 🛠️ Development

### File Structure
```
sites/
├── control/
│   ├── index.html    # Control interface
│   ├── app.js        # JavaScript functionality
│   └── README.md     # Control documentation
├── docs/
│   ├── index.html    # Documentation site
│   └── README.md     # Documentation guide
└── README.md         # This overview
```

### Adding Features
- **Control Interface:** Edit `control/app.js` and `control/index.html`
- **Documentation:** Edit `docs/index.html` for content updates
- **Styling:** Both sites use consistent CSS variables
- **Mermaid Diagrams:** Add interactive diagrams in documentation

## 🎯 Use Cases

### For End Users
- **Control Interface:** Daily matrix control and monitoring
- **Documentation:** Learning and troubleshooting reference

### For Developers
- **Control Interface:** API testing and development
- **Documentation:** Implementation reference and guides

### For Builders
- **Documentation:** Complete assembly and wiring guides
- **Control Interface:** Testing and validation tools