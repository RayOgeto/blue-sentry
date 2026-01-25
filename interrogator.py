import asyncio
import sys
from bleak import BleakClient

# Common Bluetooth UUIDs for readability
UUID_MAP = {
    "00001800-0000-1000-8000-00805f9b34fb": "Generic Access",
    "00001801-0000-1000-8000-00805f9b34fb": "Generic Attribute",
    "0000180a-0000-1000-8000-00805f9b34fb": "Device Information",
    "0000180f-0000-1000-8000-00805f9b34fb": "Battery Service",
    "0000180d-0000-1000-8000-00805f9b34fb": "Heart Rate",
    "00002a00-0000-1000-8000-00805f9b34fb": "Device Name",
    "00002a19-0000-1000-8000-00805f9b34fb": "Battery Level",
    "00002a29-0000-1000-8000-00805f9b34fb": "Manufacturer Name String",
    "00002a24-0000-1000-8000-00805f9b34fb": "Model Number String",
}

async def interrogate_device(address):
    print(f"[*] Connecting to {address}...")
    
    try:
        async with BleakClient(address) as client:
            print(f"[+] Connected to {address}")
            print(f"    Paired: {client.is_connected}")

            print("\n[*] Enumerating Services...")
            for service in client.services:
                service_name = UUID_MAP.get(str(service.uuid), "Unknown Service")
                print(f"\nSERVICE: {service.uuid} ({service_name})")
                
                for char in service.characteristics:
                    char_name = UUID_MAP.get(str(char.uuid), "Unknown Characteristic")
                    props = ",".join(char.properties)
                    print(f"  └── CHAR: {char.uuid} ({char_name})")
                    print(f"      Properties: [{props}]")

                    # Attempt to READ readable characteristics
                    if "read" in char.properties:
                        try:
                            # Standard UUIDs often contain simple strings or bytes
                            value = await client.read_gatt_char(char.uuid)
                            
                            # Try to decode as string, otherwise show hex
                            try:
                                decoded_val = value.decode('utf-8')
                            except:
                                decoded_val = value.hex()
                                
                            print(f"      >>> VALUE: {decoded_val}")
                        except Exception as e:
                            print(f"      >>> READ FAILED: {e}")

    except Exception as e:
        print(f"[-] Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 interrogator.py <MAC_ADDRESS>")
        sys.exit(1)
    
    target_mac = sys.argv[1]
    asyncio.run(interrogate_device(target_mac))