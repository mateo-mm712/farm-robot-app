"""
Device configuration for the Soil Monitoring System.

Define serial ports, baud rates, and device identifiers here.
The system can auto-detect USB devices by VID/PID for reliable operation
even if port numbers change.
"""

import serial
import serial.tools.list_ports

# ============================================================================
# USB DEVICE IDENTIFICATION BY VID/PID
# ============================================================================
# These values identify your specific hardware devices
# The system will automatically find them even if port numbers change

# Soil Sensor - Generic USB Serial Adapter (Modbus RTU)
SENSOR_VID = 0x1A86          # Vendor ID
SENSOR_PID = 0x7523          # Product ID  
SENSOR_BAUD = 9600           # Baud rate
SENSOR_SLAVE_ID = 1          # Modbus slave ID

# Relay Module - Silicon Labs CP2102N UART Bridge
RELAY_VID = 0x10C4           # Silicon Labs
RELAY_PID = 0xEA60           # CP2102N
RELAY_BAUD = 9600            # Baud rate

# ============================================================================
# FALLBACK PORTS (if auto-detection fails)
# ============================================================================
# These are used if the devices cannot be found by VID/PID
RELAY_PORT_FALLBACK = "/dev/ttyUSB0"
SENSOR_PORT_FALLBACK = "/dev/ttyUSB1"

# ============================================================================
# PROBE CONFIGURATION
# ============================================================================
PROBE_EXTENSION_TIME = 3  # Time to extend probe (seconds)

# ============================================================================
# AUTO-DETECTION FUNCTIONS
# ============================================================================

def find_device_by_vid_pid(vid, pid):
    """
    Find a USB device by its Vendor ID and Product ID.
    
    Args:
        vid: Vendor ID (integer, hex format like 0x1A86)
        pid: Product ID (integer, hex format like 0x7523)
    
    Returns:
        Device port string (e.g., '/dev/ttyUSB0') or None if not found
    """
    try:
        ports = serial.tools.list_ports.comports()
        for port in ports:
            if port.vid == vid and port.pid == pid:
                print(f"Found device (VID: 0x{vid:04X}, PID: 0x{pid:04X}) at {port.device}")
                return port.device
    except Exception as e:
        print(f"Error detecting USB devices: {e}")
    
    return None


def get_relay_port():
    """
    Auto-detect relay serial port by VID/PID.
    
    Returns:
        Port name (e.g., '/dev/ttyUSB0') or default fallback
    """
    port = find_device_by_vid_pid(RELAY_VID, RELAY_PID)
    if port:
        return port
    print(f"Relay not found by VID/PID, falling back to {RELAY_PORT_FALLBACK}")
    return RELAY_PORT_FALLBACK


def get_sensor_port():
    """
    Auto-detect soil sensor serial port by VID/PID.
    
    Returns:
        Port name (e.g., '/dev/ttyUSB1') or default fallback
    """
    port = find_device_by_vid_pid(SENSOR_VID, SENSOR_PID)
    if port:
        return port
    print(f"Sensor not found by VID/PID, falling back to {SENSOR_PORT_FALLBACK}")
    return SENSOR_PORT_FALLBACK


def list_available_ports():
    """
    List all available USB serial ports.
    
    Returns:
        List of port information dictionaries
    """
    try:
        ports = serial.tools.list_ports.comports()
        port_list = []
        for port in ports:
            port_list.append({
                "device": port.device,
                "description": port.description,
                "vid": f"0x{port.vid:04X}" if port.vid else None,
                "pid": f"0x{port.pid:04X}" if port.pid else None
            })
            print(f"  {port.device}: {port.description} (VID: 0x{port.vid:04X}, PID: 0x{port.pid:04X})")
        return port_list
    except Exception as e:
        print(f"Error listing ports: {e}")
        return []
