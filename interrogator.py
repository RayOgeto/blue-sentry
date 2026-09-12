"""
BlueSentry GATT Interrogator
Connects to a target BLE peripheral, enumerates the GATT service table,
and audits exposed characteristics and values.
"""

import asyncio
import sys
from typing import Optional

from bleak import BleakClient
from bleak.exc import BleakError
from rich.console import Console
from rich.panel import Panel
from rich.tree import Tree
from rich.table import Table

import vendors

def get_service_name(uuid_str: str) -> str:
    """Returns human-readable name for a service UUID."""
    uuid_lower = uuid_str.lower()
    return vendors.SERVICE_UUIDS.get(uuid_lower, "Custom / Unknown Service")

def get_char_name(uuid_str: str) -> str:
    """Returns human-readable name for a characteristic UUID."""
    uuid_lower = uuid_str.lower()
    return vendors.CHARACTERISTIC_UUIDS.get(uuid_lower, "Custom / Unknown Characteristic")

async def interrogate_device(address: str, console: Optional[Console] = None, timeout: float = 12.0) -> dict:
    """
    Connects to the specified BLE peripheral address and extracts GATT services.
    Outputs rich visual tree if console is provided.
    Returns structured dictionary with findings.
    """
    if console is None:
        console = Console()

    console.print(f"\n[bold yellow][*] Attempting connection to {address} (timeout {timeout}s)...[/bold yellow]")
    
    result = {
        "address": address,
        "connected": False,
        "services": [],
        "error": None
    }

    try:
        async with BleakClient(address, timeout=timeout) as client:
            result["connected"] = client.is_connected
            console.print(f"[bold green][+] Successfully connected to {address}[/bold green]")
            
            root_tree = Tree(f"[bold cyan]GATT Profile for {address}[/bold cyan]")

            for service in client.services:
                s_name = get_service_name(str(service.uuid))
                s_branch = root_tree.add(f"[bold white]Service:[/bold white] [green]{s_name}[/green] [dim]({service.uuid})[/dim]")
                service_data = {
                    "uuid": str(service.uuid),
                    "name": s_name,
                    "characteristics": []
                }

                for char in service.characteristics:
                    c_name = get_char_name(str(char.uuid))
                    props = ", ".join(char.properties)
                    char_desc = f"[cyan]{c_name}[/cyan] [dim]({char.uuid})[/dim] | Props: [[magenta]{props}[/magenta]]"
                    c_branch = s_branch.add(char_desc)

                    char_data = {
                        "uuid": str(char.uuid),
                        "name": c_name,
                        "properties": list(char.properties),
                        "value": None,
                        "read_error": None
                    }

                    # Safely attempt to read if characteristic has 'read' permission
                    if "read" in char.properties:
                        try:
                            raw_val = await client.read_gatt_char(char.uuid)
                            try:
                                # Try decoding as UTF-8 string, stripping null bytes
                                decoded_val = raw_val.decode('utf-8', errors='replace').strip('\x00')
                                display_val = f'"{decoded_val}"'
                            except Exception:
                                display_val = f"0x{raw_val.hex()}"

                            char_data["value"] = display_val
                            c_branch.add(f"[bold green]↳ Read Value:[/bold green] [yellow]{display_val}[/yellow]")
                        except Exception as read_err:
                            char_data["read_error"] = str(read_err)
                            c_branch.add(f"[dim red]↳ Read Failed:[/dim red] [dim]{read_err}[/dim]")

                    service_data["characteristics"].append(char_data)

                result["services"].append(service_data)

            console.print(Panel(root_tree, title=f"GATT Audit Report: {address}", border_style="blue"))

    except asyncio.TimeoutError:
        err_msg = f"Connection timed out after {timeout} seconds. Device may be out of range or not advertising."
        result["error"] = err_msg
        console.print(f"[bold red][-] Error:[/bold red] {err_msg}")
    except BleakError as be:
        err_msg = f"Bleak Bluetooth Error: {be}"
        result["error"] = err_msg
        console.print(f"[bold red][-] Error:[/bold red] {err_msg}")
    except Exception as ex:
        err_msg = f"Unexpected Error: {ex}"
        result["error"] = err_msg
        console.print(f"[bold red][-] Error:[/bold red] {err_msg}")

    return result

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 interrogator.py <MAC_ADDRESS>")
        sys.exit(1)

    target = sys.argv[1]
    cli_console = Console()
    try:
        asyncio.run(interrogate_device(target, console=cli_console))
    except KeyboardInterrupt:
        cli_console.print("\n[yellow]Interrogation interrupted by user.[/yellow]")