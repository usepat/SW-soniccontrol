from pymodbus.client import ModbusSerialClient
import time

client = ModbusSerialClient(
    '/dev/ttyUSB0',
    baudrate=115200,
    parity="E"
)
client.connect()
try:
    while True:
        try:
            res = client.write_registers(1024, [0x0001, 0x0000, 0x0410])
            print(res)
        except:
            print("failed")
        time.sleep(1)
finally:
    client.close()