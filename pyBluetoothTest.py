import asyncio
from bleak import BleakClient

address = "a0:dd:6c:87:88:54"  # Replace with your ESP32's MAC address
characteristic_uuid = "beb5483e-36e1-4688-b7f5-ea07361b26a8"  # Replace with your characteristic UUID

async def send_data():
    async with BleakClient(address) as client:
        print("Connected to ESP32")
        data = "Hello from Python"
        await client.write_gatt_char(characteristic_uuid, data.encode('utf-8'))
        print("Data sent:", data)

# Use asyncio.run to run the async function
asyncio.run(send_data())
