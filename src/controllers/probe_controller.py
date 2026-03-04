"""Probe controller managing sensor and relay operations."""

import time
from logs.data_logger import DataLogger


class ProbeController:
    """Manages soil probe extension, measurement, and retraction."""

    def __init__(self, soil_sensor, relay):
        """
        Initialize the probe controller.
        
        Args:
            soil_sensor: SoilSensor instance
            relay: RelayController instance
        """
        self.soil = soil_sensor
        self.relay = relay
        self.state = "IDLE"
        self.emergency_stop = False

        self.extension_time = 30  # seconds (tuned for full actuator extension)

    def trigger_estop(self):
        """Trigger emergency stop."""
        print("E-STOP TRIGGERED")
        self.emergency_stop = True
        self.relay.off()
        self.state = "ESTOP"

    def reset_estop(self):
        """Reset emergency stop."""
        self.emergency_stop = False
        self.state = "IDLE"

    def take_measurement(self):
        """
        Take a soil measurement (extend, measure, retract).
        
        Returns:
            Dictionary with soil sensor data, or None if failed
        """
        if self.state != "IDLE":
            print("System busy")
            return None

        if self.emergency_stop:
            print("Cannot operate - E-STOP active")
            return None

        try:
            self.state = "EXTENDING"
            if not self.relay.on():
                raise RuntimeError("Failed to activate relay")

            start_time = time.time()

            # Wait for extension time while checking for emergency stop
            while time.time() - start_time < self.extension_time:
                if self.emergency_stop:
                    self.relay.off()
                    self.state = "IDLE"
                    return None
                # Sleep briefly to avoid CPU spinning and allow hardware time
                time.sleep(0.1)

            self.state = "MEASURING"
            data = self.soil.read()

            self.state = "RETRACTING"
            if not self.relay.off():
                # Even if off fails, we've tried
                print("Warning: Relay off command may have failed")

            self.state = "IDLE"
            return data

        except Exception as e:
            print("Controller error:", e)
            try:
                self.relay.off()
            except:
                pass
            self.state = "ERROR"
            return None
