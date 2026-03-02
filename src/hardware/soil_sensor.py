"""Soil sensor driver for multi-parameter soil measurements."""

import serial
import struct
from typing import Optional, Dict, Any


class SoilSensor:
    """Reads soil sensor data via Modbus RTU protocol."""

    def __init__(self, port: str, baudrate: int = 9600, slave_id: int = 1):
        """
        Initialize the soil sensor.

        Args:
            port: Serial port name (e.g., '/dev/ttyUSB0')
            baudrate: Baud rate for serial communication
            slave_id: Modbus slave ID of the sensor
        """
        self.port = port
        self.baudrate = baudrate
        self.slave_id = slave_id
        self.serial: Optional[serial.Serial] = None
        self.connected = False

    def connect(self):
        """Establish connection to soil sensor."""
        try:
            self.serial = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=1.0,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                bytesize=serial.EIGHTBITS
            )
            self.connected = True
            print(f"Soil sensor connected on {self.port}")
        except serial.SerialException as e:
            print(f"Failed to connect to soil sensor: {e}")
            self.connected = False

    def _read_registers(self, start_addr: int, count: int) -> Optional[bytes]:
        """
        Read holding registers from sensor using Modbus RTU.

        Args:
            start_addr: Starting register address
            count: Number of registers to read

        Returns:
            Raw register data or None if read failed
        """
        if not self.serial or not self.connected:
            print("Sensor not connected")
            return None

        try:
            # Modbus RTU: [SlaveID][FunctionCode][StartAddr_H][StartAddr_L][Count_H][Count_L][CRC_L][CRC_H]
            request = bytes([
                self.slave_id,
                0x03,  # Read holding registers function code
                (start_addr >> 8) & 0xFF,
                start_addr & 0xFF,
                (count >> 8) & 0xFF,
                count & 0xFF
            ])

            # Calculate and append CRC16
            crc = self._calculate_crc16(request)
            request += struct.pack('<H', crc)

            self.serial.write(request)
            response = self.serial.read(2 + count * 2 + 2)  # Expected response length

            if len(response) >= 7:
                return response[3:-2]  # Extract data, skip header and CRC

        except Exception as e:
            print(f"Error reading registers: {e}")

        return None

    @staticmethod
    def _calculate_crc16(data: bytes) -> int:
        """Calculate CRC16 checksum for Modbus."""
        crc = 0xFFFF
        for byte in data:
            crc ^= byte
            for _ in range(8):
                if crc & 1:
                    crc = (crc >> 1) ^ 0xA001
                else:
                    crc >>= 1
        return crc

    def read_data(self) -> Optional[Dict[str, Any]]:
        """
        Read all soil sensor parameters.

        Returns:
            Dictionary with sensor readings or None if read failed
        """
        if not self.connected:
            print("Sensor not connected")
            return None

        try:
            # Read 8 registers (16 bytes) from address 0x00
            data = self._read_registers(0x00, 8)

            if data and len(data) >= 16:
                # Unpack sensor values (assuming 16-bit unsigned integers from sensor)
                values = struct.unpack('>8H', data)

                return {
                    "temperature": values[0] / 100.0,  # Celsius
                    "moisture": values[1] / 10.0,      # % volumetric water content
                    "ec": values[2] / 100.0,           # mS/cm conductivity
                    "ph": values[3] / 100.0,           # pH
                    "nitrogen": values[4],              # mg/kg
                    "phosphorus": values[5],            # mg/kg
                    "potassium": values[6],             # mg/kg
                    "salinity": values[7] / 100.0       # ppt
                }
            else:
                print("Invalid sensor response")
                return None

        except Exception as e:
            print(f"Error reading sensor data: {e}")
            return None

    def disconnect(self):
        """Close connection to soil sensor."""
        if self.serial and self.serial.is_open:
            self.serial.close()
            self.connected = False
            print("Soil sensor disconnected")
