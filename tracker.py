"""
BlueSentry Bloodhound Tracker
Real-time BLE signal tracker with plotext terminal graphing and
Exponential Moving Average (EMA) signal stabilization.
"""

import asyncio
from collections import deque
import sys
import time
from typing import Optional

from bleak import BleakScanner
import plotext as plt
from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Table

console = Console()

HISTORY_SIZE = 50
EMA_ALPHA = 0.35  # Smoothing factor: 0.0 < alpha <= 1.0 (higher = more reactive, lower = smoother)

class BloodhoundTracker:
    def __init__(self, target_mac: str):
        self.target_mac = target_mac.strip().upper()
        self.rssi_history = deque(maxlen=HISTORY_SIZE)
        self.timestamps = deque(maxlen=HISTORY_SIZE)
        self.smoothed_history = deque(maxlen=HISTORY_SIZE)
        
        self.current_rssi = -100
        self.smoothed_rssi: Optional[float] = None
        self.last_seen = 0.0
        self.device_name = "Unknown"
        self.packet_count = 0

    def detection_callback(self, device, advertisement_data):
        """Callback invoked by BleakScanner for each received BLE advertisement packet."""
        addr = device.address.strip().upper()
        if addr == self.target_mac:
            # Use advertisement_data.rssi as primary, fallback to device.rssi or -100
            raw_rssi = advertisement_data.rssi
            if raw_rssi is None:
                raw_rssi = getattr(device, "rssi", None)
            if raw_rssi is None:
                raw_rssi = -100

            self.current_rssi = raw_rssi
            self.last_seen = time.time()
            self.packet_count += 1
            
            # Update name if available
            dev_name = advertisement_data.local_name or device.name
            if dev_name and self.device_name == "Unknown":
                self.device_name = dev_name

    def tick(self) -> str:
        """Processes time-decay, applies EMA smoothing, and renders plotext graph."""
        now = time.time()
        
        # If no advertisement received in the last 3.5 seconds, treat signal as lost / minimum
        effective_rssi = self.current_rssi if (now - self.last_seen <= 3.5) else -100

        # Update EMA smoothed RSSI
        if self.smoothed_rssi is None or effective_rssi == -100:
            self.smoothed_rssi = float(effective_rssi)
        else:
            self.smoothed_rssi = (EMA_ALPHA * effective_rssi) + ((1.0 - EMA_ALPHA) * self.smoothed_rssi)

        self.rssi_history.append(effective_rssi)
        self.smoothed_history.append(round(self.smoothed_rssi, 1))
        self.timestamps.append(time.strftime("%H:%M:%S"))

        # Render plotext graph
        plt.clf()
        plt.plotsize(None, 14)
        if len(self.smoothed_history) > 1:
            plt.plot(list(self.smoothed_history), label="Smoothed (EMA)", color="green", marker="braille")
            plt.plot(list(self.rssi_history), label="Raw RSSI", color="yellow", marker="dot")
        else:
            plt.plot([-100], label="Signal", color="green")

        plt.ylim(-100, -30)
        plt.title(f"Bloodhound Track: {self.device_name} [{self.target_mac}]")
        plt.xlabel("Sample Time")
        plt.ylabel("RSSI (dBm)")
        plt.theme("dark")
        plt.frame(True)
        plt.grid(True, True)
        
        return plt.build()

    def get_alert_panel(self) -> Panel:
        """Returns a formatted proximity alert and stats panel."""
        active_rssi = self.smoothed_rssi if self.smoothed_rssi is not None else -100
        now = time.time()
        is_stale = (now - self.last_seen > 3.5) or (self.last_seen == 0)

        if is_stale:
            status_text = "[dim]SIGNAL LOST / OUT OF RANGE[/dim]"
            border_col = "dim"
        elif active_rssi >= -52:
            status_text = "[bold white on red] !!! VERY CLOSE (< 1m) !!! [/bold white on red]"
            border_col = "red"
        elif active_rssi >= -70:
            status_text = "[bold black on yellow] NEARBY (1m - 3m) [/bold black on yellow]"
            border_col = "yellow"
        elif active_rssi >= -88:
            status_text = "[bold white on blue] IN RANGE (3m - 10m) [/bold white on blue]"
            border_col = "blue"
        else:
            status_text = "[bold white on black] WEAK SIGNAL (> 10m) [/bold white on black]"
            border_col = "magenta"

        elapsed_since_seen = f"{round(now - self.last_seen, 1)}s ago" if self.last_seen > 0 else "Never"

        stats_table = Table.grid(expand=True)
        stats_table.add_column(justify="center")
        stats_table.add_column(justify="center")
        stats_table.add_column(justify="center")
        stats_table.add_column(justify="center")

        stats_table.add_row(
            f"[dim]Raw RSSI:[/dim] [bold]{self.current_rssi} dBm[/bold]",
            f"[dim]Smoothed:[/dim] [bold]{round(active_rssi, 1)} dBm[/bold]",
            f"[dim]Packets:[/dim] [bold]{self.packet_count}[/bold]",
            f"[dim]Last Seen:[/dim] [bold]{elapsed_since_seen}[/bold]"
        )

        content = Layout()
        content.split_column(
            Layout(Panel(status_text, style=border_col, box=None), ratio=1),
            Layout(stats_table, ratio=1)
        )

        return Panel(content, title="Proximity & Telemetry", border_style=border_col)

async def start_tracker(address: str):
    """
    Main asynchronous tracker routine.
    Spawns BleakScanner and streams the terminal UI.
    """
    tracker = BloodhoundTracker(address)
    console.print(f"[bold yellow]Initializing Bloodhound Tracker for:[/bold yellow] [cyan]{address}[/cyan]")
    console.print("[dim]Move around to locate the signal source. Press Ctrl+C to stop.[/dim]\n")

    layout = Layout()
    layout.split_column(
        Layout(name="graph", ratio=3),
        Layout(name="alert", ratio=1)
    )

    scanner = BleakScanner(detection_callback=tracker.detection_callback)
    
    try:
        await scanner.start()
        with Live(layout, refresh_per_second=4, screen=True) as live:
            while True:
                graph_output = tracker.tick()
                layout["graph"].update(Panel(graph_output, title="Signal Strength Telemetry"))
                layout["alert"].update(tracker.get_alert_panel())
                await asyncio.sleep(0.25)
    except (KeyboardInterrupt, asyncio.CancelledError):
        pass
    finally:
        try:
            await scanner.stop()
        except Exception:
            pass
        console.print(f"\n[bold red][!] Bloodhound tracking terminated for {address}[/bold red]")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        console.print("[red]Usage: python3 tracker.py <MAC_ADDRESS>[/red]")
        sys.exit(1)

    target_addr = sys.argv[1]
    try:
        asyncio.run(start_tracker(target_addr))
    except KeyboardInterrupt:
        console.print("\n[yellow]Tracker stopped.[/yellow]")
