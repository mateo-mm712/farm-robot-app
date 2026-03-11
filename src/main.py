# Copyright (c) farm-ng, inc. Amiga Development Kit License, Version 0.1
import argparse
import os
import sys
import threading
from typing import List

from amiga_package import ops

# import internal libs
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from soil_monitor import get_app

# Must come before kivy imports
os.environ["KIVY_NO_ARGS"] = "1"

# gui configs must go before any other kivy import
from kivy.config import Config  # noreorder # noqa: E402

Config.set("graphics", "resizable", False)
Config.set("graphics", "width", "1280")
Config.set("graphics", "height", "800")
Config.set("graphics", "fullscreen", "false")
Config.set("input", "mouse", "mouse,disable_on_activity")
Config.set("kivy", "keyboard_mode", "systemanddock")

# kivy imports
from kivy.app import App  # noqa: E402
from kivy.lang.builder import Builder  # noqa: E402
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import NumericProperty
from kivy.properties import BooleanProperty
from kivy.clock import Clock, mainthread

class Dashboard(BoxLayout):
    temp_val = NumericProperty(0)
    moisture_val = NumericProperty(0)
    n_val = NumericProperty(0)
    p_val = NumericProperty(0)
    k_val = NumericProperty(0)
    salinity_val = NumericProperty(0)
    ec_val = NumericProperty(0)
    ph_val = NumericProperty(0)

    battery = NumericProperty(100)

    actuator_on = BooleanProperty(False)

    def activate_actuator(self):
        """Trigger the full measurement sequence: extend actuator, measure, retract."""
        # Get the app instance
        app = App.get_running_app()
        # Call the app's measurement method
        app.trigger_measurement(self)

    #def update_values(self):
        #self.temp_val = random.randint(0, 100)
        #self.moisture_val = random.randint(0, 100)
        #self.n_val = random.randint(0, 100)
        #self.p_val = random.randint(0, 100)
        #self.k_val = random.randint(0, 100)
        #self.salinity_val = random.randint(0, 100)
        #self.ec_val = random.randint(0, 100)
        #self.ph_val = random.randint(0, 100)

        #self.battery = random.randint(50, 100)



class TemplateApp(App):
    """Base class for the main Kivy app."""

    def __init__(self) -> None:
        super().__init__()
        self.soil_app = get_app()

    def build(self):
        kv_path = os.path.join(os.path.dirname(__file__), "res", "main.kv")

        if not self.soil_app.initialize():
            print("Hardware initialized failed")

        # schedule periodic measurements using Kivy's clock so that
        # property updates happen on the main thread
        # Clock.schedule_interval(self._schedule_measurement, 5.0)  # Disabled for manual triggering

        return Builder.load_file(kv_path)

    def on_exit_btn(self) -> None:
        """Kills the running kivy application."""
        App.get_running_app().stop()
    
    def on_stop(self):
        print("Stopping application...")
        self.soil_app.cleanup()

    def trigger_measurement(self, dashboard):
        """Trigger measurement from the dashboard button press."""
        print("[BUTTON] Button pressed, triggering measurement...")
        # Set actuator as active on the dashboard
        dashboard.actuator_on = True
        # Run measurement in background thread to avoid blocking UI
        thread = threading.Thread(target=self._do_measurement_thread, args=(dashboard,))
        thread.daemon = True
        thread.start()

    def _do_measurement_thread(self, dashboard):
        """Run measurement in background thread."""
        print("[MEASUREMENT] Starting measurement in background thread...")
        try:
            data = self.soil_app.take_measurement()
            print(f"[MEASUREMENT] Got data: {data}")
            if data:
                # Apply measurement to UI from main thread
                self._apply_measurement(data, dashboard)
            else:
                print("[MEASUREMENT] No data returned, resetting actuator")
                Clock.schedule_once(lambda dt: self._reset_actuator(dashboard), 0)
        except Exception as e:
            print(f"[MEASUREMENT] Measurement error: {e}")
            import traceback
            traceback.print_exc()
            Clock.schedule_once(lambda dt: self._reset_actuator(dashboard), 0)

    def _reset_actuator(self, dashboard):
        """Reset actuator state on main thread."""
        dashboard.actuator_on = False

    @mainthread
    def _apply_measurement(self, data, dashboard=None):
        print(f"[MEASUREMENT] _apply_measurement called with data: {data}")
        if dashboard is None:
            dashboard = self.root.ids.dashboard
        # Map sensor data fields to dashboard properties
        dashboard.temp_val = data.get("temperature_c", data.get("temperature", 0))
        dashboard.moisture_val = data.get("moisture_pct", data.get("moisture", 0))
        dashboard.n_val = data.get("nitrogen", 0)
        dashboard.p_val = data.get("phosphorus", 0)
        dashboard.k_val = data.get("potassium", 0)
        dashboard.salinity_val = data.get("salinity", 0)
        dashboard.ec_val = data.get("ec", 0)
        dashboard.ph_val = data.get("ph", 0)
        dashboard.battery = data.get("battery", 95)
        # Reset actuator state after measurement
        dashboard.actuator_on = False
        print("Measurement complete - values updated and actuator reset")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="template-app")

    # Add additional command line arguments here

    args = parser.parse_args()

    # Use Kivy's normal run() method instead of async boilerplate
    TemplateApp().run()
