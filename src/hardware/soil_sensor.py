"""Soil sensor driver for multi-parameter soil measurements."""

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
        # pymodbus 3.x changed the constructor signature
        # `method` parameter has been replaced by `framer`.  The
        # default framer for serial communication is RTU, which
        # matches the old behavior.
        #
        # The signature now looks like:
        # ModbusSerialClient(port, *, framer=FramerType.RTU, baudrate=..., ...)
        # so we pass the port positionally and specify other options
        # by name.
        self.client = ModbusSerialClient(
            port,
            framer="rtu",
            baudrate=baudrate,
            parity="N",
            stopbits=1,
            bytesize=8,
            timeout=1
        )
        self.connected = False

    def connect(self):
        """Establish connection to the sensor."""
        try:
            self.connected = self.client.connect()
            if self.connected:
                print(f"Soil sensor connected on {self.port}")
            else:
                print(f"Failed to connect to soil sensor on {self.port}")
            return self.connected
        except Exception as e:
            print(f"Connection error: {e}")
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
                "temperature_f": r[0] / 10.0 * 9.0 / 5.0 + 32.0,
                "temperature_c": r[0] / 10.0,
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
