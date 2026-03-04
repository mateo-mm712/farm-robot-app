"""Relay controller for soil probe actuation."""

import serial
import time


class RelayController:
    """USB Relay controller using AT commands."""
    
    def __init__(self, port="/dev/ttyUSB0", baudrate=9600):
        """
        Initialize the relay controller.
        
        Args:
            port: Serial port for the USB relay (default: /dev/ttyUSB0)
            baudrate: Baud rate for serial communication (default: 9600)
        """
        self.port = port
        self.baudrate = baudrate
        self.ser = None
        self.command_delay = 0.5  # Delay for relay to process commands (seconds)
        self.connect()
    
    def connect(self):
        """Establish connection to the relay."""
        try:
            self.ser = serial.Serial(self.port, self.baudrate, timeout=1)
            time.sleep(2)  # Allow relay to initialize
            print(f"Relay connected on {self.port}")
        except Exception as e:
            print(f"Failed to connect to relay: {e}")
            self.ser = None
            raise
    
    def _send_command(self, command):
        """Send a command to the relay and wait for processing."""
        if not self.ser or not self.ser.is_open:
            raise RuntimeError("Relay not connected")
        
        self.ser.write(command)
        self.ser.flush()  # Ensure command is sent
        time.sleep(self.command_delay)  # Wait for relay to process
    
    def on(self):
        """Turn relay ON."""
        try:
            self._send_command(b'AT+CH1=1\r\n')
            print("Relay ON")
            return True
        except Exception as e:
            print(f"Error turning relay on: {e}")
            return False
    
    def off(self):
        """Turn relay OFF."""
        try:
            self._send_command(b'AT+CH1=0\r\n')
            print("Relay OFF")
            return True
        except Exception as e:
            print(f"Error turning relay off: {e}")
            return False
    
    def disconnect(self):
        """Close the serial connection."""
        if self.ser:
            self.ser.close()
            print("Relay disconnected")
