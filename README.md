# BlueSentry

**BlueSentry** is a passive Bluetooth Low Energy (BLE) scanner, analyzer, and tracker built with Python. It allows you to visualize the "invisible" world of BLE devices around you, analyze their broadcasts, and even track their physical location using signal strength.

This project is designed for educational purposes to demonstrate how devices broadcast their presence and what information is leaked "over the air" without pairing.

## Features

*   **Live Scanner (`scanner.py`):**
    *   Real-time detection of nearby BLE devices.
    *   Displays MAC Address, RSSI (Signal Strength), Device Name, and Manufacturer.
    *   Identifies device brands (Apple, Microsoft, Samsung) and service types (Heart Rate, Battery, etc.).
    *   Interactive menu to select and interrogate specific devices.

*   **Device Interrogator (`interrogator.py`):**
    *   Connects to a target device to enumerate exposed Services and Characteristics.
    *   Attempts to read values from readable characteristics (e.g., Device Name, Battery Level, Model Number).
    *   Useful for security auditing and understanding what data a device exposes publicly.

*   **Signal Tracker (`tracker.py`):**
    *   Live graphing of RSSI signal strength for a specific target device.
    *   Visual "Proximity Alert" (Very Close, Nearby, In Range) to help physically locate a device.
    *   Perfect for "Hide & Seek" experiments or finding lost BLE tags.

## Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd bluesentry
    ```

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## Usage

**Note:** On Linux, accessing the Bluetooth adapter usually requires root privileges. You may need to run these scripts with `sudo`.

### 1. Run the Scanner
Start here to see what's around you.

```bash
sudo python3 scanner.py
```
*   The scan runs for 15 seconds.
*   After the scan, select a device ID to interrogate it, or `0` to exit.

### 2. Interrogate a Specific Device
If you already know the MAC address of a device, you can query it directly.

```bash
sudo python3 interrogator.py <MAC_ADDRESS>
```
*   Example: `sudo python3 interrogator.py AA:BB:CC:11:22:33`

### 3. Track a Device
Use this tool to find the physical location of a device by following its signal strength.

```bash
sudo python3 tracker.py <MAC_ADDRESS>
```
*   The terminal will display a live graph. Move around with your laptop; higher signal (closer to -40) means you are getting warmer!

## Key Concepts

*   **Advertising Packets:** Data broadcast by devices to say "I'm here!" containing MAC address and payload data.
*   **RSSI (Received Signal Strength Indicator):** Used to estimate distance.
    *   `-40` to `-55`: Very Close (< 1m)
    *   `-90`: Limit of detection
*   **Manufacturer Data:** Often reveals the brand (Apple, Microsoft, etc.) even if the device name is hidden.
*   **UUIDs:** Unique identifiers defining device capabilities (Heart Rate monitor, Battery service, etc.).

## Disclaimer
This tool is for educational and research purposes only. Always respect privacy and applicable laws when monitoring wireless traffic.
