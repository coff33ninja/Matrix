#!/usr/bin/env python3
"""
import math
LED Matrix Wiring Diagram Generator
Generates Mermaid diagrams and documentation for different LED matrix configurations
"""

import json
import argparse
from datetime import datetime


class WiringDiagramGenerator:
    def __init__(self):
        self.controllers = {
            "arduino_uno": {
                "name": "Arduino Uno",
                "voltage": "5V",
                "default_pin": 6,
                "needs_level_shifter": False,
                "color": "#1a1a2e",
            },
            "arduino_nano": {
                "name": "Arduino Nano",
                "voltage": "5V",
                "default_pin": 6,
                "needs_level_shifter": False,
                "color": "#1a1a2e",
            },
            "esp32": {
                "name": "ESP32 Dev Board",
                "voltage": "3.3V",
                "default_pin": 13,
                "needs_level_shifter": True,
                "color": "#2E8B57",
            },
            "esp8266": {
                "name": "ESP8266 NodeMCU",
                "voltage": "3.3V",
                "default_pin": 2,
                "needs_level_shifter": True,
                "color": "#4169E1",
            },
        }

        self.power_supplies = {
            "5V5A": {"voltage": "5V", "current": "5A", "power": "25W"},
            "5V10A": {"voltage": "5V", "current": "10A", "power": "50W"},
            "5V20A": {"voltage": "5V", "current": "20A", "power": "100W"},
            "5V30A": {"voltage": "5V", "current": "30A", "power": "150W"},
            "5V40A": {"voltage": "5V", "current": "40A", "power": "200W"},
        }

    def calculate_power_requirements(self, width, height, brightness=128):
        """Calculate power requirements for the matrix using shared function"""
        try:
            from modules.arduino_models import calculate_power_requirements
        except ImportError:
            from arduino_models import calculate_power_requirements

        total_leds = width * height
        brightness_percent = (brightness / 255) * 100

        # Use shared calculation function
        power_data = calculate_power_requirements(total_leds, brightness_percent)

        # Add wiring-specific data
        power_data.update(
            {
                "total_leds": total_leds,
                "recommended_psu": self.get_recommended_psu(
                    power_data["recommended_psu_watts"] / 5
                ),  # Convert watts to amps at 5V
            }
        )

        return power_data

    def get_recommended_psu(self, required_current):
        """Get recommended power supply based on current requirements"""
        for psu_id, specs in self.power_supplies.items():
            if float(specs["current"].rstrip("A")) >= required_current:
                return psu_id
        return "5V40A"  # Fallback to highest capacity

    def generate_mermaid_diagram(
        self, controller, width, height, data_pin=None, psu=None
    ):
        """Generate Mermaid diagram for the specified configuration"""
        ctrl_info = self.controllers[controller]
        power_req = self.calculate_power_requirements(width, height)

        if data_pin is None:
            data_pin = ctrl_info["default_pin"]

        if psu is None:
            psu = power_req["recommended_psu"]

        psu_info = self.power_supplies.get(psu, self.power_supplies["5V40A"])

        # Start building the diagram
        diagram = f"""graph TB
    subgraph CONTROLLER["{ctrl_info['name']}"]
        CTRL_VCC["{ctrl_info['voltage']} Pin"]
        CTRL_GND["GND Pin"]
        CTRL_DATA["Pin {data_pin}"]
    end
    
    subgraph PSU["{psu} Power Supply<br/>{psu_info['current']} / {psu_info['power']}"]
        PSU_5V["5V +"]
        PSU_GND["GND -"]
    end
    
    subgraph MATRIX["LED Matrix<br/>{width}×{height} = {power_req['total_leds']} LEDs"]
        LED_VCC["VCC/5V"]
        LED_GND["GND"]
        LED_DIN["DIN"]
    end
    
    subgraph PROTECTION["Protection Components"]
        CAP["1000µF<br/>Capacitor"]
        RES["330Ω<br/>Resistor"]"""

        # Add level shifter for 3.3V controllers
        if ctrl_info["needs_level_shifter"]:
            diagram += """
        LS["74HCT125<br/>Level Shifter"]"""

        diagram += """
    end
    
    %% Power connections
    PSU_5V -->|"Heavy Wire<br/>18 AWG+"| LED_VCC
    PSU_GND -->|"Heavy Wire<br/>18 AWG+"| LED_GND
    
    %% Data connection"""

        # Data path depends on whether level shifter is needed
        if ctrl_info["needs_level_shifter"]:
            diagram += """
    CTRL_DATA --> LS
    LS --> RES
    RES --> LED_DIN
    PSU_5V --> LS"""
        else:
            diagram += """
    CTRL_DATA --> RES
    RES --> LED_DIN"""

        diagram += """
    
    %% Ground connection
    CTRL_GND --> LED_GND
    
    %% Protection
    CAP -->|"+5V"| LED_VCC
    CAP -->|"GND"| LED_GND
    
    %% Styling
    classDef controller fill:{ctrl_color},stroke:#e94560,stroke-width:3px,color:#ffffff
    classDef psu fill:#0f3460,stroke:#e94560,stroke-width:3px,color:#ffffff
    classDef matrix fill:#16213e,stroke:#e94560,stroke-width:3px,color:#ffffff
    classDef protection fill:#0f3460,stroke:#e94560,stroke-width:3px,color:#ffffff
    classDef dataPin fill:#e94560,stroke:#ffffff,stroke-width:3px,color:#ffffff
    
    class CONTROLLER controller
    class PSU psu
    class MATRIX matrix
    class PROTECTION protection
    class CTRL_DATA,LED_DIN dataPin""".format(
            ctrl_color=ctrl_info["color"]
        )

        if ctrl_info["needs_level_shifter"]:
            diagram += """
    class LS dataPin"""

        return diagram

    def generate_connection_list(
        self, controller, width, height, data_pin=None, psu=None
    ):
        """Generate detailed connection list"""
        ctrl_info = self.controllers[controller]
        power_req = self.calculate_power_requirements(width, height)

        if data_pin is None:
            data_pin = ctrl_info["default_pin"]

        if psu is None:
            psu = power_req["recommended_psu"]

        connections = f"""## Connection List for {width}×{height} LED Matrix

### Power Connections (Use heavy wire - 18 AWG or thicker):
- Power Supply 5V+ → LED Matrix VCC/5V
- Power Supply GND → LED Matrix GND
- Power Supply GND → {ctrl_info['name']} GND

### Data Connection:
- {ctrl_info['name']} Pin {data_pin} → """

        if ctrl_info["needs_level_shifter"]:
            connections += f"""74HCT125 Level Shifter → 330Ω Resistor → LED Matrix DIN
- Power Supply 5V+ → 74HCT125 VCC (to power the level shifter)

### Level Shifter Connections (74HCT125):
- VCC → Power Supply 5V+
- GND → Common Ground
- Input → {ctrl_info['name']} Pin {data_pin}
- Output → 330Ω Resistor → LED Matrix DIN"""
        else:
            connections += "330Ω Resistor → LED Matrix DIN"

        connections += f"""

### Protection Components:
- 1000µF Capacitor: + terminal to LED Matrix VCC, - terminal to LED Matrix GND
- Place capacitor as close to the LED strip as possible
- 330Ω Resistor in series with data line

### Power Requirements:
- Total LEDs: {power_req['total_leds']}
- Maximum Current: {power_req['total_current_amps']:.2f}A
- Recommended PSU: {psu} ({self.power_supplies[psu]['current']})
- Safety Margin: {power_req['safety_margin_percent']}% included in recommendation"""

        return connections

    def generate_troubleshooting_guide(self, controller):
        """Generate troubleshooting guide for the configuration"""
        ctrl_info = self.controllers[controller]

        guide = f"""## Troubleshooting Guide for {ctrl_info['name']}

### Common Issues and Solutions:

#### LEDs Not Lighting Up:
- Check power supply connections (5V+ and GND)
- Verify data pin connection (Pin should be connected to DIN through 330Ω resistor)
- Ensure power supply is adequate for the number of LEDs
- Test with a simple sketch that lights up first 10 LEDs

#### Flickering or Unstable Colors:
- Add or check 1000µF capacitor across power rails near LED strip
- Verify power supply capacity (should be 20% higher than calculated requirement)
- Check for loose connections, especially power connections
- Reduce brightness in code if power supply is marginal

#### Wrong Colors or Patterns:
- Verify LED type in code (WS2812B vs WS2811)
- Check color order (GRB vs RGB) in FastLED configuration
- Ensure proper XY mapping function for your wiring pattern"""

        if ctrl_info["needs_level_shifter"]:
            guide += f"""

#### {ctrl_info['name']} Specific Issues:
- Verify 74HCT125 level shifter connections
- Ensure level shifter is powered with 5V (not 3.3V)
- Check that {ctrl_info['name']} Pin {ctrl_info['default_pin']} is connected to level shifter input
- Verify level shifter output goes to 330Ω resistor then to LED DIN"""
        else:
            guide += f"""

#### {ctrl_info['name']} Specific Issues:
- Ensure you're using 5V power for LEDs (not 3.3V)
- Verify Pin {ctrl_info['default_pin']} is correctly defined in code
- Check USB connection for serial communication"""

        guide += """

#### Serial Communication Issues (Arduino IDE):
- Close Arduino IDE Serial Monitor before running Python scripts
- Verify correct COM port in Device Manager (Windows) or ls /dev/tty* (Linux/Mac)
- Try different baud rates (115200, 500000)
- Check USB cable (some cables are power-only)

### Testing Procedure:
1. Start with 10 LEDs maximum for initial testing
2. Use a simple solid color test (red, green, blue)
3. Verify power consumption with multimeter
4. Gradually increase LED count after confirming basic operation
5. Test with full matrix only after partial testing succeeds

### Safety Reminders:
- Always disconnect power when making wiring changes
- Use fused power supplies when possible
- Monitor temperature during extended operation
- Start with low brightness (25%) for initial testing"""

        return guide

    def generate_complete_guide(
        self, controller, width, height, data_pin=None, psu=None
    ):
        """Generate complete wiring guide"""
        ctrl_info = self.controllers[controller]
        power_req = self.calculate_power_requirements(width, height)

        if data_pin is None:
            data_pin = ctrl_info["default_pin"]

        if psu is None:
            psu = power_req["recommended_psu"]

        guide = f"""# LED Matrix Wiring Guide
# {width}×{height} Matrix with {ctrl_info['name']}

Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Configuration Summary:
- Controller: {ctrl_info['name']}
- Matrix Size: {width}×{height} ({power_req['total_leds']} LEDs)
- Data Pin: {data_pin}
- Power Supply: {psu}
- Level Shifter Required: {'Yes' if ctrl_info['needs_level_shifter'] else 'No'}

## Mermaid Wiring Diagram:
```mermaid
{self.generate_mermaid_diagram(controller, width, height, data_pin, psu)}
```

{self.generate_connection_list(controller, width, height, data_pin, psu)}

{self.generate_troubleshooting_guide(controller)}

## Additional Resources:
- FastLED Library: https://github.com/FastLED/FastLED
- WS2812B Datasheet: Available from LED strip manufacturer
- Power Supply Calculator: Use 60mA per LED maximum
- Arduino IDE: https://www.arduino.cc/en/software

---
Generated by LED Matrix Wiring Diagram Generator
"""
        return guide

    def save_guide(
        self, controller, width, height, filename=None, data_pin=None, psu=None
    ):
        """Save complete guide to file"""
        if filename is None:
            filename = f"wiring_guide_{controller}_{width}x{height}.md"

        guide = self.generate_complete_guide(controller, width, height, data_pin, psu)

        with open(filename, "w", encoding="utf-8") as f:
            f.write(guide)

        print(f"Wiring guide saved to: {filename}")
        return filename

    def export_configuration_json(
        self, controller, width, height, data_pin=None, psu=None, filename=None
    ):
        """Export wiring configuration as JSON using json module"""
        if filename is None:
            filename = f"wiring_config_{controller}_{width}x{height}.json"

        ctrl_info = self.controllers[controller]
        power_req = self.calculate_power_requirements(width, height)

        if data_pin is None:
            data_pin = ctrl_info["default_pin"]

        if psu is None:
            psu = power_req["recommended_psu"]

        psu_info = self.power_supplies.get(psu, self.power_supplies["5V40A"])

        # Create comprehensive configuration dictionary
        config_data = {
            "metadata": {
                "generated_on": datetime.now().isoformat(),
                "generator_version": "1.0.0",
                "configuration_type": "led_matrix_wiring",
            },
            "matrix_configuration": {
                "width": width,
                "height": height,
                "total_leds": power_req["total_leds"],
                "data_pin": data_pin,
            },
            "controller_configuration": {
                "type": controller,
                "name": ctrl_info["name"],
                "voltage": ctrl_info["voltage"],
                "needs_level_shifter": ctrl_info["needs_level_shifter"],
                "default_pin": ctrl_info["default_pin"],
                "color_code": ctrl_info["color"],
            },
            "power_requirements": {
                "total_current_amps": power_req["total_current_amps"],
                "recommended_psu": psu,
                "psu_specifications": psu_info,
                "safety_margin_percent": power_req["safety_margin_percent"],
                "brightness_factor": power_req["brightness_factor"],
            },
            "wiring_connections": {
                "power_connections": [
                    {
                        "from": f"PSU {psu_info['voltage']}+",
                        "to": "LED Matrix VCC",
                        "wire_gauge": "18 AWG+",
                    },
                    {
                        "from": "PSU GND",
                        "to": "LED Matrix GND",
                        "wire_gauge": "18 AWG+",
                    },
                    {
                        "from": "PSU GND",
                        "to": f"{ctrl_info['name']} GND",
                        "wire_gauge": "22 AWG",
                    },
                ],
                "data_connections": self._get_data_connections_config(
                    ctrl_info, data_pin
                ),
                "protection_components": [
                    {
                        "component": "1000µF Capacitor",
                        "connection": "Across LED Matrix power rails",
                    },
                    {
                        "component": "330Ω Resistor",
                        "connection": "In series with data line",
                    },
                ],
            },
            "component_list": self._generate_component_list(ctrl_info, psu_info),
            "assembly_notes": [
                "Use heavy gauge wire (18 AWG or thicker) for power connections",
                "Place capacitor as close to LED strip as possible",
                "Double-check polarity on all connections",
                "Test with a small number of LEDs first",
            ],
        }

        # Add level shifter configuration if needed
        if ctrl_info["needs_level_shifter"]:
            config_data["level_shifter_configuration"] = {
                "required": True,
                "type": "74HCT125",
                "connections": [
                    {"pin": "VCC", "connection": "PSU 5V+"},
                    {"pin": "GND", "connection": "Common Ground"},
                    {
                        "pin": "Input",
                        "connection": f"{ctrl_info['name']} Pin {data_pin}",
                    },
                    {"pin": "Output", "connection": "330Ω Resistor → LED Matrix DIN"},
                ],
            }

        # Save JSON configuration
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=2, ensure_ascii=False)

        print(f"Wiring configuration JSON saved to: {filename}")
        return filename

    def _get_data_connections_config(self, ctrl_info, data_pin):
        """Get data connection configuration for JSON export"""
        if ctrl_info["needs_level_shifter"]:
            return [
                {"from": f"{ctrl_info['name']} Pin {data_pin}", "to": "74HCT125 Input"},
                {"from": "74HCT125 Output", "to": "330Ω Resistor"},
                {"from": "330Ω Resistor", "to": "LED Matrix DIN"},
            ]
        else:
            return [
                {"from": f"{ctrl_info['name']} Pin {data_pin}", "to": "330Ω Resistor"},
                {"from": "330Ω Resistor", "to": "LED Matrix DIN"},
            ]

    def _generate_component_list(self, ctrl_info, psu_info):
        """Generate component list for JSON export"""
        components = [
            {"name": ctrl_info["name"], "quantity": 1, "type": "microcontroller"},
            {
                "name": f"Power Supply {psu_info['voltage']} {psu_info['current']}",
                "quantity": 1,
                "type": "power_supply",
            },
            {
                "name": "1000µF Electrolytic Capacitor",
                "quantity": 1,
                "type": "capacitor",
            },
            {"name": "330Ω Resistor", "quantity": 1, "type": "resistor"},
            {"name": "Jumper Wires", "quantity": "As needed", "type": "wire"},
            {
                "name": "Heavy Gauge Wire (18 AWG+)",
                "quantity": "For power connections",
                "type": "wire",
            },
        ]

        if ctrl_info["needs_level_shifter"]:
            components.append(
                {"name": "74HCT125 Level Shifter", "quantity": 1, "type": "logic_ic"}
            )

        return components

    def import_configuration_json(self, filename):
        """Import wiring configuration from JSON file"""
        try:
            with open(filename, "r") as f:
                config_data = json.load(f)

            # Validate JSON structure
            required_sections = [
                "metadata",
                "matrix_configuration",
                "controller_configuration",
                "power_requirements",
            ]
            for section in required_sections:
                if section not in config_data:
                    raise ValueError(f"Missing required section: {section}")

            print(f"Configuration imported from: {filename}")
            print(
                f"Matrix: {config_data['matrix_configuration']['width']}×{config_data['matrix_configuration']['height']}"
            )
            print(f"Controller: {config_data['controller_configuration']['name']}")
            print(f"Generated: {config_data['metadata']['generated_on']}")

            return config_data

        except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
            print(f"Error importing configuration: {e}")
            return None

    def generate_shopping_list_json(
        self, controller, width, height, data_pin=None, psu=None
    ):
        """Generate shopping list in JSON format"""
        ctrl_info = self.controllers[controller]
        power_req = self.calculate_power_requirements(width, height)

        if psu is None:
            psu = power_req["recommended_psu"]

        psu_info = self.power_supplies.get(psu, self.power_supplies["5V40A"])

        shopping_list = {
            "project_info": {
                "name": f"LED Matrix {width}×{height} with {ctrl_info['name']}",
                "total_leds": power_req["total_leds"],
                "estimated_cost": self._estimate_project_cost(
                    ctrl_info, psu_info, power_req["total_leds"]
                ),
            },
            "required_components": self._generate_component_list(ctrl_info, psu_info),
            "optional_components": [
                {
                    "name": "Breadboard or PCB",
                    "quantity": 1,
                    "type": "prototyping",
                    "purpose": "For permanent connections",
                },
                {
                    "name": "Heat Shrink Tubing",
                    "quantity": "As needed",
                    "type": "protection",
                    "purpose": "Protect solder joints",
                },
                {
                    "name": "Multimeter",
                    "quantity": 1,
                    "type": "tool",
                    "purpose": "Testing and troubleshooting",
                },
            ],
            "led_strip_specifications": {
                "type": "WS2812B",
                "total_leds_needed": power_req["total_leds"],
                "recommended_density": "60 LEDs/m or 144 LEDs/m",
                "estimated_length_meters": round(
                    power_req["total_leds"] / 60, 2
                ),  # Assuming 60 LEDs/m
            },
            "purchase_links": {
                "note": "Links are examples - shop around for best prices",
                "microcontroller": f"Search for '{ctrl_info['name']}' on electronics retailers",
                "power_supply": f"Search for '{psu_info['voltage']} {psu_info['current']} switching power supply'",
                "led_strip": "Search for 'WS2812B LED strip' with required length",
                "components": "Electronics component retailers (resistors, capacitors, wires)",
            },
        }

        return shopping_list

    def _estimate_project_cost(self, ctrl_info, psu_info, num_leds):
        """Estimate total project cost"""
        # Rough cost estimates in USD
        costs = {"arduino_uno": 25, "arduino_nano": 15, "esp32": 20, "esp8266": 12}

        controller_cost = costs.get(ctrl_info["name"].lower().replace(" ", "_"), 20)
        psu_cost = (
            int(psu_info["power"].replace("W", "")) * 0.5
        )  # Rough estimate: $0.50 per watt
        led_cost = num_leds * 0.10  # Rough estimate: $0.10 per LED
        component_cost = 15  # Resistors, capacitors, wires, etc.

        if ctrl_info["needs_level_shifter"]:
            component_cost += 5  # Level shifter IC

        total_cost = controller_cost + psu_cost + led_cost + component_cost
        return round(total_cost, 2)


def main():
    parser = argparse.ArgumentParser(description="Generate LED Matrix Wiring Diagrams")
    parser.add_argument(
        "controller",
        choices=["arduino_uno", "arduino_nano", "esp32", "esp8266"],
        help="Controller type",
    )
    parser.add_argument("width", type=int, help="Matrix width in LEDs")
    parser.add_argument("height", type=int, help="Matrix height in LEDs")
    parser.add_argument("--data-pin", type=int, help="Data pin number")
    parser.add_argument(
        "--psu",
        choices=["5V5A", "5V10A", "5V20A", "5V30A", "5V40A"],
        help="Power supply specification",
    )
    parser.add_argument("--output", help="Output filename")
    parser.add_argument(
        "--diagram-only", action="store_true", help="Output only the Mermaid diagram"
    )

    args = parser.parse_args()

    generator = WiringDiagramGenerator()

    if args.diagram_only:
        diagram = generator.generate_mermaid_diagram(
            args.controller, args.width, args.height, args.data_pin, args.psu
        )
        print(diagram)
    else:
        guide_filename = generator.save_guide(
            args.controller,
            args.width,
            args.height,
            args.output,
            args.data_pin,
            args.psu,
        )

        # Also print summary and generate JSON configuration
        power_req = generator.calculate_power_requirements(args.width, args.height)
        ctrl_info = generator.controllers[args.controller]

        print(f"\nConfiguration Summary:")
        print(f"  Controller: {ctrl_info['name']}")
        print(f"  Matrix: {args.width}×{args.height} = {power_req['total_leds']} LEDs")
        print(f"  Max Current: {power_req['total_current_amps']:.2f}A")
        print(f"  Recommended PSU: {power_req['recommended_psu']}")
        print(
            f"  Level Shifter: {'Required' if ctrl_info['needs_level_shifter'] else 'Not needed'}"
        )

        # Generate JSON configuration file
        json_filename = generator.export_configuration_json(
            args.controller, args.width, args.height, args.data_pin, args.psu
        )

        # Generate shopping list
        shopping_list = generator.generate_shopping_list_json(
            args.controller, args.width, args.height, args.data_pin, args.psu
        )

        shopping_filename = (
            f"shopping_list_{args.controller}_{args.width}x{args.height}.json"
        )
        with open(shopping_filename, "w") as f:
            json.dump(shopping_list, f, indent=2)

        print(f"  JSON Config: {json_filename}")
        print(f"  Shopping List: {shopping_filename}")
        print(f"  Estimated Cost: ${shopping_list['project_info']['estimated_cost']}")


if __name__ == "__main__":
    main()
