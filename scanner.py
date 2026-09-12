"""
BlueSentry Scanner
Passive Bluetooth Low Energy (BLE) surveillance dashboard,
radar visualization, and device auditing tool.
"""

import argparse
import asyncio
import csv
from datetime import datetime
import math
import sys
import time
from typing import Dict, List, Tuple

from bleak import BleakScanner
from rich import box
from rich.align import Align
from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

import interrogator
import tracker
import vendors

console = Console()

# In-memory dictionary for detected devices: {mac_address: {data_fields}}
detected_devices: Dict[str, dict] = {}

BANNER = r"""
[bold blue]
    ____  __            _____            __
   / __ )/ /_  _____   / ___/___  ____  / /________  __
   / __  / / / / / _ \  \__ \/ _ \/ __ \/ __/ ___/ / / /
  / /_/ / / /_/ /  __/ ___/ /  __/ / / / /_/ /  / /_/ /
/_____/_/\__,_/\___/ /____/\___/_/ /_/\__/_/   \__, /
                                              /____/
[/bold blue][dim]       v1.0.0 | Security & Privacy Auditing | @BlueSentry[/dim]
"""

def process_device(device, advertisement_data):
    """
    Callback function invoked by BleakScanner on each received advertisement.
    Parses payload into pure data without UI markup.
    """
    # 1. Device Name
    dev_name = advertisement_data.local_name or device.name or "Unknown"

    # 2. RSSI
    rssi = advertisement_data.rssi
    if rssi is None:
        rssi = getattr(device, "rssi", None)
    if rssi is None:
        rssi = -100

    # 3. Manufacturer Data
    manufacturer = "Unknown"
    man_data_raw = advertisement_data.manufacturer_data
    if man_data_raw:
        m_id = list(man_data_raw.keys())[0]
        m_bytes = man_data_raw[m_id]
        if m_id == 76:  # Apple Inc.
            manufacturer = vendors.identify_apple_device(m_bytes)
        else:
            manufacturer = vendors.COMPANY_IDS.get(m_id, f"Vendor ID: {m_id}")

    # 4. Service UUID Resolution (Pure Strings)
    services_detected: List[str] = []
    for s_uuid in advertisement_data.service_uuids:
        s_lower = str(s_uuid).lower()
        if s_lower in vendors.SERVICE_UUIDS:
            services_detected.append(vendors.SERVICE_UUIDS[s_lower])
        else:
            services_detected.append(str(s_uuid)[:8])

    # 5. Privacy & MAC Address Analysis
    addr_info = vendors.classify_address(device.address)

    # Store clean, unstyled data
    existing = detected_devices.get(device.address)
    first_seen = existing["FirstSeen"] if existing else time.strftime("%H:%M:%S")

    detected_devices[device.address] = {
        "Address": device.address,
        "FirstSeen": first_seen,
        "LastSeen": time.strftime("%H:%M:%S"),
        "Name": dev_name,
        "RSSI": rssi,
        "Manufacturer": manufacturer,
        "Services": services_detected,
        "IsRandom": addr_info["is_random"],
        "AddressType": addr_info["type_name"],
        "Tag": addr_info["tag"],
        "RawManufacturerData": man_data_raw
    }

def generate_radar_view(sorted_devices: List[Tuple[str, dict]]) -> Panel:
    """
    Renders an ASCII radial proximity map.
    Maps RSSI signal strength to distance from center.
    """
    width = 60
    height = 15
    center_x = width // 2
    center_y = height // 2

    grid = [[" " for _ in range(width)] for _ in range(height)]

    # Crosshairs
    for x in range(width):
        grid[center_y][x] = "-"
    for y in range(height):
        grid[y][center_x] = "|"
    grid[center_y][center_x] = "[bold white]@[/bold white]"  # You are here

    # Plot up to top 10 strongest signals
    top_devices = sorted_devices[:10]
    total_top = len(top_devices)

    for i, (addr, data) in enumerate(top_devices):
        rssi = data["RSSI"]
        # Normalize RSSI (-100 dBm to -30 dBm) to factor 0.0 (closest) -> 1.0 (farthest)
        dist_factor = (rssi + 30) / -70.0
        dist_factor = max(0.0, min(1.0, dist_factor))

        angle = (i * (2.0 * math.pi)) / max(total_top, 1)
        radius_x = dist_factor * (width // 2 - 2)
        radius_y = dist_factor * (height // 2 - 1)

        pos_x = int(center_x + radius_x * math.cos(angle))
        pos_y = int(center_y + radius_y * math.sin(angle))

        pos_x = max(0, min(width - 1, pos_x))
        pos_y = max(0, min(height - 1, pos_y))

        color = "green" if rssi > -60 else "yellow" if rssi > -80 else "red"
        grid[pos_y][pos_x] = f"[{color}]{i + 1}[/{color}]"

    radar_str = "\n".join("".join(row) for row in grid)
    subtitle = "[dim](Radial map is based on signal strength proximity; not physical azimuth)[/dim]"
    return Panel(
        Align.center(radar_str),
        title="[bold green]RADAR (Proximity Visualization)[/bold green]",
        subtitle=subtitle,
        box=box.ROUNDED
    )

def generate_table(sorted_devices: List[Tuple[str, dict]]) -> Table:
    """Generates the Rich Table with dynamic styling."""
    table = Table(box=box.SIMPLE, show_header=True, header_style="bold blue")

    table.add_column("ID", width=3, justify="right")
    table.add_column("Address", style="dim")
    table.add_column("Type", width=5, justify="center")
    table.add_column("RSSI", justify="right", width=6)
    table.add_column("Name / Manufacturer", style="white")
    table.add_column("Services / Tags", style="dim")

    for idx, (address, data) in enumerate(sorted_devices):
        rssi_val = data["RSSI"]
        rssi_color = "green" if rssi_val > -60 else "yellow" if rssi_val > -80 else "red"

        # Format Name and Manufacturer
        name_display = data["Name"]
        if data["Manufacturer"] != "Unknown":
            name_display += f" ([cyan]{data['Manufacturer']}[/cyan])"

        # Format privacy tag
        if data["Tag"] == "RAND":
            type_tag = "[green]RAND[/green]"
        elif data["Tag"] == "PUB":
            type_tag = "[red]PUB[/red]"
        else:
            type_tag = "[dim]UNK[/dim]"

        # Format service hints
        styled_services = []
        for s in data["Services"]:
            if "Heart Rate" in s:
                styled_services.append("[red]Heart Rate[/red]")
            elif "Battery" in s:
                styled_services.append("[yellow]Battery[/yellow]")
            elif "Human Interface" in s or "HID" in s:
                styled_services.append("[magenta]HID[/magenta]")
            elif "Fast Pair" in s:
                styled_services.append("[blue]Fast Pair[/blue]")
            elif "Tile" in s:
                styled_services.append("[green]Tile[/green]")
            elif "Exposure" in s:
                styled_services.append("[bold white on red]COVID[/bold white on red]")
            else:
                styled_services.append(s.split(" ")[0])

        services_str = ", ".join(styled_services)

        table.add_row(
            str(idx + 1),
            address,
            type_tag,
            f"[{rssi_color}]{rssi_val}[/{rssi_color}]",
            name_display,
            services_str
        )

    return table

def get_layout(sorted_devices: List[Tuple[str, dict]]) -> Layout:
    """Combines table and radar into a split view."""
    layout = Layout()
    layout.split_column(
        Layout(name="top", ratio=2),
        Layout(name="bottom", ratio=1)
    )
    layout["top"].update(Panel(generate_table(sorted_devices), title="BlueSentry Live Feed", border_style="blue"))
    layout["bottom"].update(generate_radar_view(sorted_devices))
    return layout

def save_log_to_file(filename: str = None):
    """Saves session discoveries to a pure, clean CSV file without UI markup."""
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"sentry_log_{timestamp}.csv"

    try:
        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "Address",
                "Name",
                "Manufacturer",
                "Last RSSI",
                "Services",
                "Address Type",
                "Is Randomized",
                "First Seen",
                "Last Seen"
            ])

            for addr, data in detected_devices.items():
                is_rand_str = "Yes" if data["IsRandom"] is True else ("No" if data["IsRandom"] is False else "Unknown")
                writer.writerow([
                    addr,
                    data["Name"],
                    data["Manufacturer"],
                    data["RSSI"],
                    "; ".join(data["Services"]),
                    data["AddressType"],
                    is_rand_str,
                    data["FirstSeen"],
                    data["LastSeen"]
                ])
        console.print(f"[bold green][+] Session log saved successfully:[/bold green] {filename}")
    except Exception as e:
        console.print(f"[bold red][-] Failed to save log:[/bold red] {e}")

async def interrogate_target(target_mac: str):
    """Bridges GATT interrogation into the scanner interface."""
    console.clear()
    await interrogator.interrogate_device(target_mac, console=console)
    Prompt.ask("\nPress [bold white]Enter[/bold white] to return to menu")

async def show_interactive_menu():
    """Displays post-scan interactive action menu."""
    while True:
        console.clear()
        console.print(Panel("[bold green]BlueSentry Scan Complete[/bold green]", style="green"))

        sorted_devs = sorted(detected_devices.items(), key=lambda x: x[1]["RSSI"], reverse=True)
        if not sorted_devs:
            console.print("[yellow]No devices found during scan.[/yellow]")
            return

        # Display compact summary table
        summary_table = Table(box=box.SIMPLE, show_header=True)
        summary_table.add_column("ID", width=4, justify="right")
        summary_table.add_column("Address", style="cyan")
        summary_table.add_column("RSSI", justify="right")
        summary_table.add_column("Name / Manufacturer")

        for idx, (addr, data) in enumerate(sorted_devs):
            summary_table.add_row(
                str(idx + 1),
                addr,
                str(data["RSSI"]),
                f"{data['Name']} ({data['Manufacturer']})"
            )
        console.print(summary_table)

        console.print("\n[bold cyan]ACTIONS:[/bold cyan]")
        console.print("1. [bold white]Interrogate[/bold white] (Connect & Dump GATT Services)")
        console.print("2. [bold red]BLOODHOUND[/bold red] (Track Target Signal Strength)")
        console.print("0. Exit")

        choice = Prompt.ask("Select Action", choices=["1", "2", "0"], default="0")
        if choice == "0":
            break

        target_input = Prompt.ask("Enter Device ID from the list above")
        if not target_input.isdigit():
            console.print("[red]Invalid selection: must be a number.[/red]")
            time.sleep(1)
            continue

        idx = int(target_input) - 1
        if not (0 <= idx < len(sorted_devs)):
            console.print("[red]Invalid selection: ID out of range.[/red]")
            time.sleep(1)
            continue

        target_mac = sorted_devs[idx][0]

        if choice == "1":
            await interrogate_target(target_mac)
        elif choice == "2":
            try:
                await tracker.start_tracker(target_mac)
            except KeyboardInterrupt:
                pass
            Prompt.ask("\nPress [bold white]Enter[/bold white] to return to menu")

async def run_scan(args):
    """Main scanning workflow."""
    console.print(BANNER)
    console.print("[bold yellow]Initializing BlueSentry BLE Engine...[/bold yellow]")
    console.print(f"[dim]Mode: {'Passive (Automated Logging)' if args.passive else 'Interactive Dashboard'}[/dim]")
    console.print(f"[dim]Duration: {args.duration}s | Log Destination: {args.output or 'Auto-generated timestamp'}[/dim]\n")

    scanner = BleakScanner(detection_callback=process_device)

    try:
        await scanner.start()
        start_t = time.time()
        end_t = start_t + args.duration

        if not args.passive:
            # Interactive terminal live view
            initial_sorted = sorted(detected_devices.items(), key=lambda x: x[1]["RSSI"], reverse=True)
            with Live(get_layout(initial_sorted), refresh_per_second=4, screen=True) as live:
                while time.time() < end_t:
                    sorted_devs = sorted(detected_devices.items(), key=lambda x: x[1]["RSSI"], reverse=True)
                    live.update(get_layout(sorted_devs))
                    await asyncio.sleep(0.3)
        else:
            # Passive background logging
            console.print("[green][*] Passive surveillance active. Listening for packets...[/green]")
            while time.time() < end_t:
                await asyncio.sleep(1.0)

    except KeyboardInterrupt:
        console.print("\n[bold yellow][!] Scan aborted by user.[/bold yellow]")
    except Exception as e:
        console.print(f"\n[bold red][!] Critical BLE Error:[/bold red] {e}")
    finally:
        try:
            await scanner.stop()
        except Exception:
            pass
        save_log_to_file(args.output)

    if not args.passive:
        await show_interactive_menu()

def main_entry():
    """Console scripts entry point."""
    parser = argparse.ArgumentParser(
        description="BlueSentry: Advanced BLE Scanner, Analyzer & Tracker",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog="""EXAMPLES:
  1. Standard Interactive Scan (20 seconds):
     sudo bluesentry

  2. Custom Duration (60s) with custom log path:
     sudo bluesentry --duration 60 --output audit_room.csv

  3. Passive Headless Monitoring (Surveillance):
     sudo bluesentry --passive --duration 3600 --output overnight.csv

  4. Track target signal directly:
     sudo python3 tracker.py AA:BB:CC:11:22:33
"""
    )

    parser.add_argument("-t", "--duration", type=int, default=20, help="Scan duration in seconds (default: 20)")
    parser.add_argument("-o", "--output", type=str, help="Output CSV filename (default: sentry_log_TIMESTAMP.csv)")
    parser.add_argument("-p", "--passive", action="store_true", help="Run in passive headless mode (no TUI, just log)")

    args = parser.parse_args()

    try:
        asyncio.run(run_scan(args))
    except KeyboardInterrupt:
        console.print("\n[yellow]BlueSentry exited.[/yellow]")
    except Exception as e:
        console.print(f"[bold red]Fatal Error:[/bold red] {e}")

if __name__ == "__main__":
    main_entry()
