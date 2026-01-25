import asyncio
import sys
from bleak import BleakScanner, BleakClient
from rich.console import Console
from rich.live import Live
from rich.table import Table
from rich.prompt import Prompt
from rich import box
import time

# Initialize Rich Console
console = Console()

# Dictionary to store detected devices: {address: {data...}}
detected_devices = {}

# Common Bluetooth UUIDs for interrogation
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

def process_device(device, advertisement_data):
    """
    Callback function that triggers whenever a BLE device is seen.
    It parses the raw data into a readable format.
    """
    
    # 1. Device Name: Often "Unknown" if the device relies on Scan Response to give its name
    dev_name = device.name or advertisement_data.local_name or "Unknown"
    
    # 2. RSSI: Signal Strength.
    rssi = advertisement_data.rssi or -100
    
    # 3. Manufacturer Data: The "Secret Sauce"
    manufacturer = "Unknown"
    if advertisement_data.manufacturer_data:
        m_id = list(advertisement_data.manufacturer_data.keys())[0]
        if m_id == 76:
            manufacturer = "Apple (iBeacon/AirTag?)"
        elif m_id == 6:
            manufacturer = "Microsoft"
        elif m_id == 117:
            manufacturer = "Samsung"
        else:
            manufacturer = f"ID: {m_id}"

    # 4. Service UUIDs: Hints at what the device DOES
    services = [str(s) for s in advertisement_data.service_uuids]
    service_hint = "Generic"
    if "0000180d-0000-1000-8000-00805f9b34fb" in services:
        service_hint = "[red]Heart Rate[/red]"
    elif "0000180f-0000-1000-8000-00805f9b34fb" in services:
        service_hint = "[yellow]Battery[/yellow]"
    elif "0000110b-0000-1000-8000-00805f9b34fb" in services:
        service_hint = "[blue]Audio Sink[/blue]"

    # Store/Update the device data
    detected_devices[device.address] = {
        "Time": time.strftime("%H:%M:%S"),
        "Name": dev_name,
        "RSSI": rssi,
        "Manufacturer": manufacturer,
        "Services": service_hint,
        "DeviceObj": device  # Keep the object for connecting later
    }

def generate_table():
    """Generates the Rich Table for the Live Display."""
    table = Table(title="BlueSentry: Live Bluetooth Analyzer", box=box.SIMPLE_HEAVY)

    table.add_column("ID", style="bold cyan", width=3)
    table.add_column("Address (MAC)", style="cyan")
    table.add_column("RSSI", justify="right")
    table.add_column("Device Name", style="green")
    table.add_column("Manufacturer", style="magenta")
    table.add_column("Analysis", style="bold white")

    # Sort by RSSI (Strongest signal on top)
    sorted_devices = sorted(detected_devices.items(), key=lambda x: x[1]['RSSI'], reverse=True)

    for idx, (address, data) in enumerate(sorted_devices):
        # Color code RSSI
        rssi_val = data['RSSI']
        rssi_color = "green" if rssi_val > -60 else "yellow" if rssi_val > -80 else "red"
        
        table.add_row(
            str(idx + 1),
            address,
            f"[{rssi_color}]{rssi_val} dBm[/{rssi_color}]",
            data['Name'],
            data['Manufacturer'],
            data['Services']
        )
    return table

async def interrogate_target(address):
    """Connects to a specific target and dumps GATT table."""
    console.print(f"\n[bold yellow][*] Interrogating Target:[/bold yellow] {address}")
    console.print("[dim]Connecting... (This may take a few seconds)[/dim]")

    try:
        async with BleakClient(address) as client:
            console.print(f"[bold green][+] Connected successfully![/bold green]")
            console.print(f"    Paired: {client.is_connected}")

            console.print("\n[bold white][*] Dumping Service Table:[/bold white]")
            for service in client.services:
                service_name = UUID_MAP.get(str(service.uuid), "Unknown Service")
                console.print(f"\n[bold cyan]SERVICE:[/bold cyan] {service.uuid} ({service_name})")
                
                for char in service.characteristics:
                    char_name = UUID_MAP.get(str(char.uuid), "Unknown Characteristic")
                    props = ",".join(char.properties)
                    console.print(f"  └── [yellow]CHAR:[/yellow] {char.uuid} ({char_name})")
                    console.print(f"      Properties: [{props}]")

                    if "read" in char.properties:
                        try:
                            value = await client.read_gatt_char(char.uuid)
                            try:
                                decoded_val = value.decode('utf-8')
                            except:
                                decoded_val = f"HEX: {value.hex()}"
                            console.print(f"      >>> [bold green]VALUE LEAKED:[/bold green] {decoded_val}")
                        except Exception as e:
                            console.print(f"      >>> [dim]Read Failed (Protected)[/dim]")

    except Exception as e:
        console.print(f"[bold red][-] Connection Failed:[/bold red] {e}")
        console.print("[dim]Note: Device might be out of range or rejecting connections.[/dim]")

async def run_scan():
    """Main async loop."""
    console.print("[bold yellow]Starting BlueSentry Scanner (15s)...[/bold yellow]")
    
    scanner = BleakScanner(detection_callback=process_device)
    await scanner.start()
    
    # Run the live display
    with Live(generate_table(), refresh_per_second=4) as live:
        try:
            start_time = time.time()
            while time.time() - start_time < 15:
                live.update(generate_table())
                await asyncio.sleep(0.5)
        except KeyboardInterrupt:
            pass
        finally:
            await scanner.stop()
            console.print("\n[bold green]Scan Complete.[/bold green]")

    # Interactive Menu
    sorted_devices = sorted(detected_devices.items(), key=lambda x: x[1]['RSSI'], reverse=True)
    
    if not sorted_devices:
        console.print("No devices found.")
        return

    console.print("\n[bold]Post-Scan Actions:[/bold]")
    console.print("Enter the [bold cyan]ID[/bold cyan] of a device to interrogate, or [bold]0[/bold] to exit.")
    
    choice = Prompt.ask("Selection")
    
    if choice.isdigit():
        idx = int(choice) - 1
        if 0 <= idx < len(sorted_devices):
            target_mac = sorted_devices[idx][0]
            await interrogate_target(target_mac)
        else:
            console.print("Exiting.")
    else:
        console.print("Invalid selection.")

if __name__ == "__main__":
    try:
        asyncio.run(run_scan())
    except KeyboardInterrupt:
        pass
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        console.print("[dim]Note: You might need to run this with 'sudo' on Linux.[/dim]")
