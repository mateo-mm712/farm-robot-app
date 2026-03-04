from pymodbus.client.serial import ModbusSerialClient

class SoilSensor:
    def __init__(self, port, baudrate, slave_id):
        self.slave_id = slave_id
        self.client = ModbusSerialClient(
            method="rtu",
            port=port,
            baudrate=baudrate,
            parity="N",
            stopbits=1,
            bytesize=8,
            timeout=1
        )

    def connect(self):
        return self.client.connect()

    def read(self):
        result = self.client.read_holding_registers(
            address=0,
            count=8,
            slave=self.slave_id
        )

        if result.isError():
            raise RuntimeError("Soil sensor read failed")

        r = result.registers

        return {
            "temperature_c": r[0] / 10.0* 9.0 / 5.0 + 32.0,
            "moisture_pct": r[1] / 10.0,
            "ec": r[2],
            "ph": r[3] / 10.0,
            "nitrogen": r[4],
            "phosphorus": r[5],
            "potassium": r[6],
            "salinity": r[7],
        }
