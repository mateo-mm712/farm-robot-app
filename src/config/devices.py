"""Device configuration and serial port detection."""

import serial.tools.list_ports
from typing import Optional

# Serial communication parameters
RELAY_BAUD = 9600
SENSOR_BAUD = 9600
SENSOR_SLAVE_ID = 1

# USB VID/PID for device detection (these should be updated based on actual hardware)
RELAY_VID_PID = (0x10C4, 0xEA60)      # CP2102 USB to UART
SENSOR_VID_PID = (0x10C4, 0xEA60)     # CP2102 USB to UART

# Fallback ports if auto-detection fails
DEFAULT_RELAY_PORT = "/dev/ttyUSB0"
DEFAULT_SENSOR_PORT = "/dev/ttyUSB1"


def get_relay_port() -> str:
    """
    Auto-detect relay serial port by VID/PID.

    Returns:
        Port name (e.g., '/dev/ttyUSB0') or default fallback
    """
    return _find_port_by_vid_pid(RELAY_VID_PID) or DEFAULT_RELAY_PORT


def get_sensor_port() -> str:
    """
    Auto-detect soil sensor serial port by VID/PID.

    Returns:
        Port name (e.g., '/dev/ttyUSB1') or default fallback
    """
    return _find_port_by_vid_pid(SENSOR_VID_PID) or DEFAULT_SENSOR_PORT


def _find_port_by_vid_pid(vid_pid: tuple) -> Optional[str]:
    """
    Find serial port by USB VID/PID.

    Args:
        vid_pid: Tuple of (VID, PID)

    Returns:
        Port name or None if not found
    """
    try:
        ports = serial.tools.list_ports.comports()
        for port in ports:
            if port.vid and port.pid:
                if (port.vid, port.pid) == vid_pid:
                    print(f"Found device at {port.device}: {port.description}")
                    return port.device
    except Exception as e:
        print(f"Error detecting USB devices: {e}")

    return None


def list_available_ports() -> list:
    """
    List all available serial ports.

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
                "vid": port.vid,
                "pid": port.pid
            })
        return port_list
    except Exception as e:
        print(f"Error listing ports: {e}")
        return []
