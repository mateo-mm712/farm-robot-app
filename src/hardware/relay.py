"""Relay controller for soil probe actuation."""

import serial
from typing import Optional


class RelayController:
    """Controls a relay module via serial communication."""

    def __init__(self, port: str, baudrate: int = 9600):
        """
        Initialize the relay controller.

        Args:
            port: Serial port name (e.g., '/dev/ttyUSB0')
            baudrate: Baud rate for serial communication
        """
        self.port = port
        self.baudrate = baudrate
        self.serial: Optional[serial.Serial] = None
        self._connect()

    def _connect(self):
        """Establish serial connection to relay."""
        try:
            self.serial = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=1.0
            )
            print(f"Relay connected on {self.port}")
        except serial.SerialException as e:
            print(f"Failed to connect to relay: {e}")
            self.serial = None

    def on(self):
        """Turn relay on."""
        if self.serial and self.serial.is_open:
            try:
                self.serial.write(b'\xFF\x01\x01')  # Command to turn ON
                print("Relay ON")
            except serial.SerialException as e:
                print(f"Error sending relay ON command: {e}")

    def off(self):
        """Turn relay off."""
        if self.serial and self.serial.is_open:
            try:
                self.serial.write(b'\xFF\x01\x00')  # Command to turn OFF
                print("Relay OFF")
            except serial.SerialException as e:
                print(f"Error sending relay OFF command: {e}")

    def disconnect(self):
        """Close serial connection."""
        if self.serial and self.serial.is_open:
            self.off()
            self.serial.close()
            print("Relay disconnected")
