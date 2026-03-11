"""
Amiga Soil Monitor - Main Application Entry Point

This module initializes the hardware (soil sensor and relay) and the probe controller.
The Kivy GUI should import and use these components.
"""

import sys
import os

# Add current directory to path for local imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from hardware.relay import RelayController
from hardware.soil_sensor import SoilSensor
from controllers.probe_controller import ProbeController
from config.devices import (
    get_relay_port, get_sensor_port,
    RELAY_BAUD, SENSOR_BAUD, SENSOR_SLAVE_ID
)
from logs.data_logger import DataLogger


class SoilMonitorApp:
    """Main application class that manages the soil monitoring system."""
    
    def __init__(self):
        """Initialize the soil monitor application."""
        self.relay = None
        self.soil_sensor = None
        self.controller = None
        self.data_logger = None
        
        self._initialized = False
    
    def initialize(self):
        """
        Initialize all hardware components.
        
        Returns:
            bool: True if GUI can load, False only for critical errors
        """
        try:
            print("Initializing Soil Monitoring System...")
            
            # Try to initialize relay
            relay_ok = False
            try:
                print("Detecting relay...")
                relay_port = get_relay_port()
                print(f"Connecting to relay on {relay_port}...")
                self.relay = RelayController(port=relay_port, baudrate=RELAY_BAUD)
                relay_ok = True
            except Exception as e:
                print(f"WARNING: Failed to connect to relay: {e}")
            
            # Try to initialize soil sensor
            sensor_ok = False
            try:
                print("Detecting soil sensor...")
                sensor_port = get_sensor_port()
                print(f"Connecting to soil sensor on {sensor_port}...")
                self.soil_sensor = SoilSensor(
                    port=sensor_port,
                    baudrate=SENSOR_BAUD,
                    slave_id=SENSOR_SLAVE_ID
                )
                connected = self.soil_sensor.connect()
                if connected:
                    sensor_ok = True
                else:
                    # raise to trigger the outer exception handler so we log
                    # the failure consistently
                    raise RuntimeError(f"could not open sensor on {sensor_port}")
            except Exception as e:
                print(f"WARNING: Failed to connect to soil sensor: {e}")
            
            # Only initialize controller if we have both devices
            if relay_ok and sensor_ok:
                self.controller = ProbeController(self.soil_sensor, self.relay)
                print("Probe controller initialized")
            else:
                print("WARNING: Operating in GUI-only mode (missing hardware)")
            
            # Initialize data logger
            self.data_logger = DataLogger()
            
            self._initialized = True
            print("System initialized!")
            return True
            
        except Exception as e:
            print(f"Fatal initialization error: {e}")
            self.cleanup()
            return False
    
    def take_measurement(self):
        """
        Trigger a soil measurement.
        
        Returns:
            dict or None: Measurement data, or None if failed
        """
        if not self._initialized:
            print("System not initialized")
            return None
        
        if not self.controller:
            print("WARNING: Hardware not connected, cannot take measurement")
            return None
        
        try:
            data = self.controller.take_measurement()
            if data and self.data_logger:
                self.data_logger.log(data)
            return data
        except Exception as e:
            print(f"Measurement failed: {e}")
            return None
    
    def get_status(self):
        """
        Get current system status.
        
        Returns:
            dict: Status information
        """
        return {
            "initialized": self._initialized,
            "controller_state": self.controller.state if self.controller else "UNINITIALIZED",
            "emergency_stop": self.controller.emergency_stop if self.controller else False,
            "sensor_connected": self.soil_sensor.connected if self.soil_sensor else False,
        }
    
    def emergency_stop(self):
        """Trigger emergency stop."""
        if self.controller:
            self.controller.trigger_estop()
    
    def reset_emergency_stop(self):
        """Reset emergency stop."""
        if self.controller:
            self.controller.reset_estop()
    
    def cleanup(self):
        """Clean up and disconnect all hardware."""
        print("Cleaning up...")
        
        if self.relay:
            try:
                self.relay.off()
                self.relay.disconnect()
            except Exception as e:
                print(f"Error disconnecting relay: {e}")
        
        if self.soil_sensor:
            try:
                self.soil_sensor.disconnect()
            except Exception as e:
                print(f"Error disconnecting sensor: {e}")
        
        self._initialized = False
        print("Cleanup complete")


# Global application instance
_app_instance = None


def get_app():
    """Get the global SoilMonitorApp instance (singleton pattern)."""
    global _app_instance
    if _app_instance is None:
        _app_instance = SoilMonitorApp()
    return _app_instance


def main():
    """
    Main entry point for testing without GUI.
    
    To use with Kivy GUI, import get_app() and call app.initialize(),
    then use app.take_measurement() and other methods as needed.
    """
    app = get_app()
    
    if not app.initialize():
        print("Failed to initialize application")
        return 1
    
    try:
        # Example: take a single measurement
        print("\nTaking initial measurement...")
        data = app.take_measurement()
        
        if data:
            print("\nSoil Data:")
            for key, value in data.items():
                print(f"  {key}: {value}")
        else:
            print("Failed to read soil data")
    
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    
    except Exception as e:
        print(f"Error: {e}")
    
    finally:
        app.cleanup()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
