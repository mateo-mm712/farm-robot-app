"""Soil sensor driver for multi-parameter soil measurements."""

import os

from pymodbus.client.serial import ModbusSerialClient


class SoilSensor:
    """USB Soil sensor using Modbus RTU protocol."""
    
    def __init__(self, port, baudrate, slave_id):
        """
        Initialize the soil sensor.
        
        Args:
            port: Serial port for the USB sensor (e.g., /dev/ttyUSB1)
            baudrate: Baud rate for serial communication (default: 9600)
            slave_id: Modbus slave ID for the sensor (default: 1)
        """
        self.port = port
        self.baudrate = baudrate
        self.slave_id = slave_id
        # The underlying ModbusSerialClient is not created until we actually
        # try to connect.  Creating it eagerly in __init__ could open and lock
        # the serial port immediately, which we want to avoid (especially since
        # the port may be busy or may succeed only after we clear a stale lock).
        self.client: ModbusSerialClient | None = None
        self.connected = False

    def _remove_stale_lock(self):
        """Delete any leftover pyserial lock file for this port.

        PySerial creates `/var/lock/LCK..<dev>` when opening a port exclusively.
        If a previous process crashed or we opened the device earlier in the
        same process the lock file may persist and prevent future opens.
        Removing it is safe on our embedded system since nothing else should
        legitimately be using the sensor port.
        """
        lockfile = f"/var/lock/LCK..{os.path.basename(self.port)}"
        if os.path.exists(lockfile):
            try:
                os.remove(lockfile)
                print(f"Removed stale lock file {lockfile}")
            except OSError:
                pass

    def connect(self):
        """Establish connection to the sensor.

        Returns:
            bool: True if the connection succeeds, False otherwise.
        """
        # attempt to create the Modbus client and connect inside the same
        # try/except so that any errors from the constructor (which may open
        # and lock the port) are also handled.
        # Attempt to connect, catching both False return and exceptions.
        if self.client is None:
            # client creation itself may raise if the port cannot be opened;
            # perform it inside our recovery loop below as well.
            self.client = ModbusSerialClient(
                self.port,
                framer="rtu",
                baudrate=self.baudrate,
                parity="N",
                stopbits=1,
                bytesize=8,
                timeout=1
            )

        success = False
        try:
            success = self.client.connect()
        except Exception as e:
            # pymodbus swallows most errors, but the constructor above or
            # connect() itself may still bubble exceptions such as lock
            # failures.  Log them so the user can see what happened.
            print(f"Connection exception: {e}")
            success = False

        if success:
            self.connected = True
            print(f"Soil sensor connected on {self.port}")
            return True

        # initial attempt failed; try to recover from stale lock
        print(f"Initial connection to {self.port} failed, attempting lock recovery")
        self._remove_stale_lock()
        try:
            if self.client:
                self.client.close()
        except Exception:
            pass
        # rebuild the client and retry
        self.client = ModbusSerialClient(
            self.port,
            framer="rtu",
            baudrate=self.baudrate,
            parity="N",
            stopbits=1,
            bytesize=8,
            timeout=1
        )
        try:
            success = self.client.connect()
        except Exception as e2:
            print(f"Retry connection exception: {e2}")
            success = False

        if success:
            self.connected = True
            print(f"Soil sensor connected on {self.port} (after clearing lock)")
            return True

        print(f"Soil sensor connection failed after retry on {self.port}")
        return False

    def read(self):
        """
        Read soil data from the sensor.
        
        Returns:
            Dictionary containing sensor readings, or None if read fails
        """
        if not self.connected:
            raise RuntimeError("Soil sensor not connected")
            
        try:
            result = self.client.read_holding_registers(
                address=0,
                count=8,
                slave=self.slave_id
            )

            if result.isError():
                raise RuntimeError("Soil sensor read failed")

            r = result.registers

            return {
                "temperature_f": round(r[0] / 10.0 * 9.0 / 5.0 + 32.0, 1),
                "moisture_pct": r[1] / 10.0,
                "ec": r[2],
                "ph": r[3] / 10.0,
                "nitrogen": r[4],
                "phosphorus": r[5],
                "potassium": r[6],
                "salinity": r[7],
            }
        except Exception as e:
            print(f"Error reading sensor: {e}")
            return None

    def read_data(self):
        """Alias for read() to maintain compatibility."""
        return self.read()

    def disconnect(self):
        """Close the connection to the sensor."""
        if self.client:
            self.client.close()
            self.connected = False
            print("Soil sensor disconnected")
