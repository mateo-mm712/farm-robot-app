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
import random

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

    def update_values(self):
        #self.temp_val = random.randint(0, 100)
        #self.moisture_val = random.randint(0, 100)
        #self.n_val = random.randint(0, 100)
        #self.p_val = random.randint(0, 100)
        #self.k_val = random.randint(0, 100)
        #self.salinity_val = random.randint(0, 100)
        #self.ec_val = random.randint(0, 100)
        #self.ph_val = random.randint(0, 100)

        self.battery = random.randint(50, 100)



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

        return Builder.load_file(kv_path)

    def on_exit_btn(self) -> None:
        """Kills the running kivy application."""
        App.get_running_app().stop()

    async def app_func(self):
        async def run_wrapper() -> None:
            # we don't actually need to set asyncio as the lib because it is
            # the default, but it doesn't hurt to be explicit
            await self.async_run(async_lib="asyncio")
            for task in self.async_tasks:
                task.cancel()

        # Placeholder task
        self.async_tasks.append(asyncio.ensure_future(self.template_function()))

        return await asyncio.gather(run_wrapper(), *self.async_tasks)

    async def template_function(self) -> None:
        while not self.root:
            await asyncio.sleep(0.01)
            
        dashboard = self.root.ids.dashboard
        loop = asyncio.get_running_loop()
        
        while True:
            await asyncio.sleep(5.0)  # adjust measurement interval
            
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
