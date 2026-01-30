import asyncio
import sys
import time
import plotext as plt
from bleak import BleakScanner
from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel

console = Console()

# Configuration
HISTORY_SIZE = 50
rssi_history = []
timestamps = []

target_device = {
    "rssi": -100,
    "last_seen": 0,
    "name": "Unknown"
}

def detection_callback(device, advertisement_data):
    """Callback for when the specific target is found."""
    # Note: We filter in the main loop, but we need to update global state here
    if device.address.upper() == TARGET_MAC.upper():
        target_device["rssi"] = device.rssi
        target_device["last_seen"] = time.time()
        target_device["name"] = device.name or advertisement_data.local_name or "Unknown"

def update_graph():
    """Draws the plotext graph and returns it as a string."""
    plt.clf()
    
    # Data management
    current_rssi = target_device["rssi"]
    
    # If device hasn't been seen in 3 seconds, drop signal to -100
    if time.time() - target_device["last_seen"] > 3.0:
        current_rssi = -100

    rssi_history.append(current_rssi)
    timestamps.append(time.strftime("%H:%M:%S"))
    
    # Keep history fixed size
    if len(rssi_history) > HISTORY_SIZE:
        rssi_history.pop(0)
        timestamps.pop(0)

    # Plotting
    plt.plot(rssi_history, marker="dot", color="green")
    plt.ylim(-100, -30)
    plt.title(f"Signal Strength: {target_device['name']} ({TARGET_MAC})")
    plt.xlabel("Time")
    plt.ylabel("RSSI (dBm)")
    plt.theme("dark")  # clear, dark, matrix
    plt.frame(True)
    plt.grid(True, True)
    
    return plt.build()

def get_proximity_alert(rssi):
    """Returns a rich panel with hot/cold text."""
    if rssi > -50:
        return Panel("[bold white on red] !!! VERY CLOSE !!! [/bold white on red]", title="Proximity", border_style="red")
    elif rssi > -70:
        return Panel("[bold black on yellow] NEARBY [/bold black on yellow]", title="Proximity", border_style="yellow")
    elif rssi > -90:
        return Panel("[bold white on blue] IN RANGE [/bold white on blue]", title="Proximity", border_style="blue")
    else:
        return Panel("[dim] WEAK / LOST SIGNAL [/dim]", title="Proximity", border_style="dim")

async def start_tracker(address):
    """
    Starts the tracker for a specific MAC address.
    Can be called from other scripts.
    """
    global TARGET_MAC
    TARGET_MAC = address
    
    # Clear internal history for a fresh start
    rssi_history.clear()
    timestamps.clear()
    target_device["rssi"] = -100
    target_device["last_seen"] = 0
    target_device["name"] = "Unknown"

    # Setup Rich Layout
    layout = Layout()
    layout.split_column(
        Layout(name="graph", ratio=3),
        Layout(name="alert", ratio=1)
    )

    console.print(f"[bold yellow]Tracking Device:[/bold yellow] {address}")
    console.print("Move around to locate the signal source. Press Ctrl+C to stop.")

    scanner = BleakScanner(detection_callback=detection_callback)
    await scanner.start()

    try:
        with Live(layout, refresh_per_second=4) as live:
            while True:
                # Update Graph
                graph_str = update_graph()
                layout["graph"].update(Panel(graph_str, title="Live Signal Tracker"))
                
                # Update Proximity Alert
                rssi = rssi_history[-1] if rssi_history else -100
                layout["alert"].update(get_proximity_alert(rssi))
                
                await asyncio.sleep(0.2)
    except KeyboardInterrupt:
        pass
    except asyncio.CancelledError:
        pass
    finally:
        await scanner.stop()
        console.print("[bold red]Tracker Stopped.[/bold red]")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 tracker.py <MAC_ADDRESS>")
        sys.exit(1)
    
    target_mac = sys.argv[1]
    try:
        asyncio.run(start_tracker(target_mac))
    except KeyboardInterrupt:
        pass
