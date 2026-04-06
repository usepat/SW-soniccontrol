from pymodbus.client import ModbusSerialClient

client = ModbusSerialClient(
    '/dev/ttyUSB0',
    baudrate=19200,
    parity="E"
)
client.connect()
res = client.write_registers(1024, [0x0001, 0x0000, 0x0411])
print(res)
client.close()