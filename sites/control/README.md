# LED Matrix Control Interface

Real-time control interface for your LED matrix project. This interface provides direct control over your matrix hardware with live preview and monitoring capabilities.

## 🎮 Features

- **Real-time LED control** with live matrix preview
- **Pattern generation** (Solid, Rainbow, Plasma, Fire, Matrix Rain)
- **Arduino code generator** with board comparison
- **Wiring diagram generator** with power calculations
- **Configuration management** with backup/restore
- **System monitoring** with live stats

## 🚀 Quick Start

1. **Start the Python controller:**
   ```bash
   python matrix.py controller
   ```

2. **Start the control interface:**
   ```bash
   python matrix.py web --control
   ```

3. **Access the interface:**
   Open your browser to `http://localhost:3000`

## 🔌 API Integration

This interface connects to the Python controller's API server (port 8080) for:
- Real-time matrix control
- Hardware communication
- Configuration management
- System monitoring

## 📱 Mobile Support

The interface is fully responsive and works on:
- Desktop computers
- Tablets
- Mobile phones
- Any modern web browser

## 🔗 Related

- **Documentation:** See `../docs/` for comprehensive project documentation
- **Python Controller:** Main application with GUI and API server
- **Hardware Setup:** Refer to documentation for wiring and assembly guides