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
from kivy.uix.label import Label
from kivy.uix.screenmanager import ScreenManager, Screen
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
        history_kv_path = os.path.join(os.path.dirname(__file__), "res", "history.kv")

        if not self.soil_app.initialize():
            print("Hardware initialized failed")

        # Load both KV files
        Builder.load_file(history_kv_path)
        return Builder.load_file(kv_path)

    def show_history(self) -> None:
        """Switch to history screen and refresh entries."""
        self.root.ids.screen_manager.current = "history"
        history_screen = self.root.ids.history_screen
        if hasattr(history_screen, 'load_history'):
            history_screen.load_history()

    def show_dashboard(self) -> None:
        """Switch back to dashboard screen."""
        self.root.ids.screen_manager.current = "dashboard"

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
        dashboard.temp_val = data.get("temperature_f", data.get("temperature", 0))
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


class HistoryScreen(BoxLayout):
    """Screen that shows historical logged soil measurements."""

    def load_history(self):
        app = App.get_running_app()
        data_logger = app.soil_app.data_logger if hasattr(app, 'soil_app') else None
        measurements = []
        if data_logger:
            measurements = data_logger.get_latest_measurements(20)

        history_container = self.ids.history_list
        history_container.clear_widgets()

        if not measurements:
            history_container.add_widget(Label(text="No historical measurements available.", size_hint_y=None, height=40))
            return

        # Show most recent first
        for m in reversed(measurements):
            display_text = (
                f"{m.get('timestamp','')} | "
                f"T={m.get('temperature','')} "
                f"M={m.get('moisture','')} "
                f"pH={m.get('ph','')} "
                f"EC={m.get('ec','')} "
                f"N={m.get('nitrogen','')} "
                f"P={m.get('phosphorus','')} "
                f"K={m.get('potassium','')} "
                f"Sal={m.get('salinity','')} "
                f"Bat={m.get('battery','')}"
            )
            history_container.add_widget(Label(text=display_text, size_hint_y=None, height=30, text_size=(self.width, None), halign='left', valign='middle'))


if __name__ == "__main__":

    parser = argparse.ArgumentParser(prog="template-app")

    # Add additional command line arguments here

    args = parser.parse_args()

    # Use Kivy's normal run() method instead of async boilerplate
    TemplateApp().run()
