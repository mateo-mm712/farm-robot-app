# Copyright (c) farm-ng, inc. Amiga Development Kit License, Version 0.1
import argparse
import asyncio
import os
from typing import List

from amiga_package import ops

# import internal libs

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
from soil_monitor import get_app

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
        self.actuator_on = not self.actuator_on
        print("ACTUANTOR ON" if self.actuator_on else "ACTUATOR OFF")

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

        self.async_tasks: List[asyncio.Task] = []
        self.soil_app = get_app()

    def build(self):
        kv_path = os.path.join(os.path.dirname(__file__), "res", "main.kv")

        if not self.soil_app.initialize():
            print("Hardware initialized failed")

        # schedule periodic measurements using Kivy's clock so that
        # property updates happen on the main thread
        from kivy.clock import Clock
        Clock.schedule_interval(self._schedule_measurement, 5.0)

        return Builder.load_file(kv_path)

    def on_exit_btn(self) -> None:
        """Kills the running kivy application."""
        App.get_running_app().stop()

    # the async/app_func boilerplate is no longer required; we can use
    # Kivy's normal run() and let the clock handle scheduling.  Keep the
    # method around in case someone still wants to start the app via
    # asyncio, but it isn't needed for simple GUI updates.

    async def app_func(self):
        async def run_wrapper() -> None:
            await self.async_run(async_lib="asyncio")
            for task in self.async_tasks:
                task.cancel()

        # keep existing behaviour as a fallback, but don't create any
        # periodic task here since the clock is doing it now
        return await run_wrapper()

    # this coroutine is no longer used for periodic updates; the clock
    # callbacks manage the work. leave it for backwards compatibility.
    async def template_function(self):
        while not self.root:
            await asyncio.sleep(0.01)

        dashboard = self.root.ids.dashboard
        loop = asyncio.get_running_loop()

        while True:
            await asyncio.sleep(5.0)  # adjust measurement interval

            try:
                # Run blocking sensor call in background thread
                data = await loop.run_in_executor(None, self.soil_app.take_measurement)

                if data:
                    dashboard.temp_val = data.get("temperature", 0)
                    dashboard.moisture_val = data.get("moisture", 0)
                    dashboard.n_val = data.get("nitrogen", 0)
                    dashboard.p_val = data.get("phosphorus", 0)
                    dashboard.k_val = data.get("potassium", 0)
                    dashboard.salinity_val = data.get("salinity", 0)
                    dashboard.ec_val = data.get("ec", 0)
                    dashboard.ph_val = data.get("ph", 0)
                    dashboard.battery = data.get("battery", 0)

                    print("Measurement Updated")

            except Exception as e:
                print(f"Measurement error: {e}")
    
    def on_stop(self):
        print("Stopping application...")
        self.soil_app.cleanup()

    # --------------------------------------------------
    # new helpers for the clock-based updater
    # --------------------------------------------------
    def _schedule_measurement(self, dt: float) -> None:
        """Called by Kivy's Clock on the main thread every ``dt`` seconds."""
        # dispatch the blocking I/O to a thread pool so the UI stays
        # responsive.
        loop = asyncio.get_event_loop()
        asyncio.ensure_future(self._do_measurement(loop))

    async def _do_measurement(self, loop):
        data = await loop.run_in_executor(None, self.soil_app.take_measurement)
        if not data or not self.root:
            return
        # update widget properties on main thread (already there, but use
        # mainthread decorator for clarity)
        self._apply_measurement(data)

    from kivy.clock import mainthread
    @mainthread
    def _apply_measurement(self, data):
        dashboard = self.root.ids.dashboard
        dashboard.temp_val = data.get("temperature", 0)
        dashboard.moisture_val = data.get("moisture", 0)
        dashboard.n_val = data.get("nitrogen", 0)
        dashboard.p_val = data.get("phosphorus", 0)
        dashboard.k_val = data.get("potassium", 0)
        dashboard.salinity_val = data.get("salinity", 0)
        dashboard.ec_val = data.get("ec", 0)
        dashboard.ph_val = data.get("ph", 0)
        dashboard.battery = data.get("battery", 0)
        print("Measurement Updated")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="template-app")

    # Add additional command line arguments here

    args = parser.parse_args()

    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(TemplateApp().app_func())
    except asyncio.CancelledError:
        pass
    loop.close()
