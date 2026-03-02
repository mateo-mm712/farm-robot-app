"""Probe controller managing sensor and relay operations."""

from typing import Optional, Dict, Any
from enum import Enum


class ControllerState(Enum):
    """States for the probe controller."""
    IDLE = "IDLE"
    MEASURING = "MEASURING"
    ERROR = "ERROR"
    ESTOP = "ESTOP"


class ProbeController:
    """Manages coordinated sensor and relay operations."""

    def __init__(self, soil_sensor, relay):
        """
        Initialize the probe controller.

        Args:
            soil_sensor: SoilSensor instance
            relay: RelayController instance
        """
        self.soil_sensor = soil_sensor
        self.relay = relay
        self.state = ControllerState.IDLE
        self.emergency_stop = False

    def take_measurement(self) -> Optional[Dict[str, Any]]:
        """
        Take a soil measurement.

        Procedure:
        1. Activate relay to probe
        2. Wait for sensor to stabilize
        3. Read sensor data
        4. Deactivate relay
        5. Return data with battery level

        Returns:
            Dictionary with sensor readings and battery, or None if failed
        """
        if self.emergency_stop:
            print("Emergency stop active - cannot measure")
            return None

        try:
            self.state = ControllerState.MEASURING

            # Activate relay to insert probe
            self.relay.on()

            # Allow sensor to stabilize (in real implementation, use asyncio.sleep)
            import time
            time.sleep(1.0)

            # Read sensor data
            data = self.soil_sensor.read_data()

            # Deactivate relay
            self.relay.off()

            if data:
                # Add battery level (placeholder - would be read from sensor in production)
                data["battery"] = 95

                self.state = ControllerState.IDLE
                return data
            else:
                self.state = ControllerState.ERROR
                return None

        except Exception as e:
            print(f"Measurement error: {e}")
            self.state = ControllerState.ERROR
            self.relay.off()
            return None

    def trigger_estop(self):
        """Trigger emergency stop."""
        self.emergency_stop = True
        self.state = ControllerState.ESTOP
        self.relay.off()
        print("Emergency stop triggered!")

    def reset_estop(self):
        """Reset emergency stop."""
        self.emergency_stop = False
        self.state = ControllerState.IDLE
        print("Emergency stop reset")
