import asyncio
import sys
import csv
import math
import time
from datetime import datetime

from bleak import BleakScanner, BleakClient
from rich.console import Console
from rich.live import Live
from rich.table import Table
from rich.prompt import Prompt
from rich import box
from rich.layout import Layout
from rich.panel import Panel
from rich.align import Align
from rich.text import Text

import vendors  # Our database
import tracker  # Our tracking module

# Initialize Rich Console
console = Console()

# Dictionary to store detected devices: {address: {data...}}
detected_devices = {}

def process_device(device, advertisement_data):
    """
    Callback function that triggers whenever a BLE device is seen.
    Parses raw data into a readable format and applies heuristics.
    """
    
    # 1. Device Name
    dev_name = device.name or advertisement_data.local_name or "Unknown"
    
    # 2. RSSI
    rssi = advertisement_data.rssi or -100
    
    # 3. Manufacturer Analysis (De-Anonymization)
    manufacturer = "Unknown"
    man_data_raw = advertisement_data.manufacturer_data
    
    if man_data_raw:
        m_id = list(man_data_raw.keys())[0]
        m_bytes = man_data_raw[m_id]
        
        if m_id == 76: # Apple
            manufacturer = vendors.identify_apple_device(m_bytes)
        else:
            manufacturer = vendors.COMPANY_IDS.get(m_id, f"ID: {m_id}")

    # 4. Service UUIDs
    services = [str(s) for s in advertisement_data.service_uuids]
    service_hints = []
    
    for s in services:
        if s in vendors.SERVICE_UUIDS:
            name = vendors.SERVICE_UUIDS[s]
            if "Heart Rate" in name: service_hints.append("[red]Heart Rate[/red]")
            elif "Battery" in name: service_hints.append("[yellow]Battery[/yellow]")
            elif "Human Interface" in name: service_hints.append("[magenta]HID[/magenta]")
            elif "Google" in name: service_hints.append("[blue]Fast Pair[/blue]")
            elif "Tile" in name: service_hints.append("[green]Tile[/green]")
            elif "Exposure" in name: service_hints.append("[bold white on red]COVID[/bold white on red]")
            else: service_hints.append(name.split(" ")[0])
            
    service_str = ", ".join(service_hints) if service_hints else ""

    # 5. Privacy Check
    try:
        first_byte = int(device.address.split(":")[0], 16)
        is_random = (first_byte & 0x02) == 0x02
        privacy_status = "[green]RAND[/green]" if is_random else "[red]PUBLIC[/red]"
    except:
        privacy_status = "?"

    # Store/Update
    detected_devices[device.address] = {
        "Time": time.strftime("%H:%M:%S"),
        "Name": dev_name,
        "RSSI": rssi,
        "Manufacturer": manufacturer,
        "Services": service_str,
        "Privacy": privacy_status,
        "RawData": man_data_raw  # For logging
    }

def generate_radar_view():
    """
    Creates a text-based 'Radar' visualization.
    We map RSSI to distance from center.
    """
    # Canvas size
    width = 60
    height = 15
    center_x = width // 2
    center_y = height // 2
    
    # Create an empty grid
    grid = [[" " for _ in range(width)] for _ in range(height)]
    
    # Draw crosshairs
    for x in range(width): grid[center_y][x] = "-"
    for y in range(height): grid[y][center_x] = "|"
    grid[center_y][center_x] = "[bold white]@[/bold white]" # You are here
    
    # Plot devices
    sorted_devices = sorted(detected_devices.items(), key=lambda x: x[1]['RSSI'], reverse=True)
    
    # Limit to top 10 strongest signals to avoid clutter
    for i, (addr, data) in enumerate(sorted_devices[:10]):
        rssi = data['RSSI']
        
        # Normalize RSSI (-100 to -30) to distance (0 to 1)
        # Stronger signal (-30) = Closer (0 distance)
        # Weaker signal (-100) = Farther (1 distance)
        dist_factor = (rssi + 30) / -70.0 
        dist_factor = max(0, min(1, dist_factor))
        
        # Calculate visuals
        # We vary angle based on index to spread them out visually (fake angle)
        angle = (i * (2 * 3.14159)) / min(len(sorted_devices), 10)
        
        # Radius in characters
        radius_x = dist_factor * (width // 2 - 2)
        radius_y = dist_factor * (height // 2 - 1)
        
        pos_x = int(center_x + radius_x * math.cos(angle))
        pos_y = int(center_y + radius_y * math.sin(angle))
        
        # Clamp
        pos_x = max(0, min(width - 1, pos_x))
        pos_y = max(0, min(height - 1, pos_y))
        
        # Marker
        symbol = str(i + 1) # ID number
        color = "green" if rssi > -60 else "yellow" if rssi > -80 else "red"
        
        grid[pos_y][pos_x] = f"[{color}]{symbol}[/{color}]"

    # Convert grid to string
    radar_str = ""
    for row in grid:
        radar_str += "".join(row) + "\n"
        
    return Panel(Align.center(radar_str), title="[bold green]RADAR (Proximity Visualization)[/bold green]", box=box.ROUNDED)

def generate_table():
    """Generates the Rich Table."""
    table = Table(box=box.SIMPLE, show_header=True, header_style="bold blue")

    table.add_column("ID", width=3)
    table.add_column("Address", style="dim")
    table.add_column("T", width=4, justify="center") # Type
    table.add_column("RSSI", justify="right")
    table.add_column("Name / Manufacturer", style="white")
    table.add_column("Tags", style="dim")

    sorted_devices = sorted(detected_devices.items(), key=lambda x: x[1]['RSSI'], reverse=True)

    for idx, (address, data) in enumerate(sorted_devices):
        rssi_val = data['RSSI']
        rssi_color = "green" if rssi_val > -60 else "yellow" if rssi_val > -80 else "red"
        
        # Combine Name and Manufacturer for compact view
        name_display = data['Name']
        if data['Manufacturer'] != "Unknown":
            name_display += f" ([cyan]{data['Manufacturer']}[/cyan])"
            
        table.add_row(
            str(idx + 1),
            address,
            data['Privacy'].replace("RAND", "R").replace("PUBLIC", "P"),
            f"[{rssi_color}]{rssi_val}[/{rssi_color}]",
            name_display,
            data['Services']
        )
    return table

def get_layout():
    layout = Layout()
    layout.split_column(
        Layout(name="top", ratio=2),
        Layout(name="bottom", ratio=1)
    )
    layout["top"].update(Panel(generate_table(), title="BlueSentry Live Feed", border_style="blue"))
    layout["bottom"].update(generate_radar_view())
    return layout

import argparse

# ... (Imports remain the same) ...

# [Keep existing helper functions: process_device, generate_radar_view, generate_table, get_layout, save_log, interrogate_target]

async def run_scan(args):
    console.print(f"[bold yellow]Initializing BlueSentry System...[/bold yellow]")
    console.print(f"[dim]Mode: {'Passive (No Interaction)' if args.passive else 'Interactive'}[/dim]")
    console.print(f"[dim]Duration: {args.duration}s | Output: {args.output}[/dim]")
    
    scanner = BleakScanner(detection_callback=process_device)
    
    try:
        await scanner.start()
        
        # Determine loop duration
        start_t = time.time()
        end_t = start_t + args.duration
        
        with Live(get_layout(), refresh_per_second=4, screen=True) as live:
            while time.time() < end_t:
                live.update(get_layout())
                await asyncio.sleep(0.5)
                
    except KeyboardInterrupt:
        console.print("\n[bold yellow]Scan interrupted by user.[/bold yellow]")
    except Exception as e:
        console.print(f"\n[bold red]CRITICAL ERROR:[/bold red] {e}")
    finally:
        try:
            await scanner.stop()
        except:
            pass
        
        # AUTO-SAVE LOG (Crash Safe)
        # We pass the custom filename if provided
        save_log_to_file(args.output) 

    # POST SCAN MENU (Only if not passive)
    if not args.passive:
        await show_interactive_menu()

def save_log_to_file(filename=None):
    """Saves the session to a CSV file."""
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"sentry_log_{timestamp}.csv"
    
    try:
        with open(filename, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["Address", "Name", "Manufacturer", "Last RSSI", "Services", "Privacy"])
            
            for addr, data in detected_devices.items():
                writer.writerow([
                    addr, 
                    data['Name'], 
                    data['Manufacturer'], 
                    data['RSSI'], 
                    data['Services'],
                    data['Privacy']
                ])
        console.print(f"[bold green]Session Log Saved:[/bold green] {filename}")
    except Exception as e:
        console.print(f"[bold red]Failed to save log:[/bold red] {e}")

async def show_interactive_menu():
    console.clear()
    console.print(Panel("[bold]Scan Complete[/bold]", style="green"))
    
    sorted_devs = sorted(detected_devices.items(), key=lambda x: x[1]['RSSI'], reverse=True)
    if not sorted_devs: 
        console.print("No devices found.")
        return

    while True:
        console.print("\n[bold cyan]ACTIONS:[/bold cyan]")
        console.print("1. [bold white]Interrogate[/bold white] (Connect & Dump Info)")
        console.print("2. [bold red]BLOODHOUND[/bold red] (Track Signal Strength)")
        console.print("0. Exit")
        
        choice = Prompt.ask("Select Action", choices=["1", "2", "0"])
        
        if choice == "0":
            break
            
        target_idx = Prompt.ask("Enter Device ID from last scan")
        if not target_idx.isdigit(): continue
        
        idx = int(target_idx) - 1
        if not (0 <= idx < len(sorted_devs)): 
            console.print("[red]Invalid ID[/red]")
            continue
            
        target_mac = sorted_devs[idx][0]
        
        if choice == "1":
            await interrogate_target(target_mac)
        elif choice == "2":
            # Launch Tracker
            try:
                await tracker.start_tracker(target_mac)
            except KeyboardInterrupt:
                pass

# ... (Imports)

BANNER = r"""
[bold blue]
    ____  __            _____            __
   / __ )/ /_  _____   / ___/___  ____  / /________  __
  / __  / / / / / _ \  \__ \/ _ \/ __ \/ __/ ___/ / / /
 / /_/ / / /_/ /  __/ ___/ /  __/ / / / /_/ /  / /_/ /
/_____/_/\__,_/\___/ /____/\___/_/ /_/\__/_/   \__, /
                                              /____/
[/bold blue][dim]       v1.0.0 | Production Ready | @BlueSentryTeam[/dim]
"""

# ... (Previous code remains until main_entry)

def main_entry():
    # Custom Help Formatter to allow newlines in description
    parser = argparse.ArgumentParser(
        description="BlueSentry: Advanced BLE Scanner, Analyzer & Tracker",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog="""[bold]EXAMPLES:[/bold]
  [green]1. Standard Scan (20s):[/green]
     sudo bluesentry

  [green]2. Long Scan (60s) with custom log file:[/green]
     sudo bluesentry --duration 60 --output results.csv

  [green]3. Passive Mode (Background Surveillance):[/green]
     sudo bluesentry --passive --duration 3600

  [green]4. Track a specific device (Bloodhound):[/green]
     sudo python3 tracker.py AA:BB:CC:11:22:33
"""
    )
    
    parser.add_argument("-t", "--duration", type=int, default=20, help="Scan duration in seconds (default: 20)")
    parser.add_argument("-o", "--output", type=str, help="Output CSV filename (default: sentry_log_TIMESTAMP.csv)")
    parser.add_argument("-p", "--passive", action="store_true", help="Run in passive mode (no interactive menu, just log)")
    
    args = parser.parse_args()

    # Print Banner
    console.print(BANNER)

    try:
        asyncio.run(run_scan(args))
# ... (Rest of file)
    except KeyboardInterrupt:
        pass
    except Exception as e:
        console.print(f"[red]Fatal Error:[/red] {e}")

if __name__ == "__main__":
    main_entry()
