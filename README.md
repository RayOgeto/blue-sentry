# BlueSentry

**BlueSentry** is an advanced, production-ready Bluetooth Low Energy (BLE) scanner, analyzer, and tracker. It goes beyond simple scanning by providing real-time "Radar" visualization, detailed device fingerprinting (including Apple "Continuity" protocol analysis), and a built-in signal tracker ("Bloodhound" mode).

![Status](https://img.shields.io/badge/Status-Production%20Ready-brightgreen)
![Python](https://img.shields.io/badge/Python-3.8+-blue)

## Features

### 📡 Advanced Scanner (`bluesentry`)
*   **Live Radar Visualization:** A real-time, text-based radar display showing nearby devices relative to your position based on signal strength.
*   **Privacy Analysis:** Automatically detects if a device is using a **Randomized** (Private) or **Public** (Trackable) MAC address.
*   **De-Anonymization:** Identifies specific Apple devices (AirTags, AirPods, AirDrop, etc.) and other major brands (Fitbit, Tile, Garmin) even when they don't broadcast a name.
*   **Sentry Mode (Auto-Logging):** Every scan automatically saves a CSV log of all detected devices, ensuring no data is lost even if the app crashes.

### 🐕 Bloodhound Tracker
*   **Signal Tracking:** A "Hot/Cold" game for physical device location.
*   **Graphing:** Live RSSI graph to visualize signal trends.
*   **Proximity Alerts:** Visual alerts when you are "Very Close" to the target.

### 🔬 Interrogator
*   **Deep Inspection:** Connects to devices to dump their GATT Service Table.
*   **Data Leaks:** Attempts to read standard characteristics to find exposed data (Device Name, Battery Level, etc.).

## Installation

### Option 1: Quick Run (No Install)
```bash
# Clone the repo
git clone <repository_url>
cd bluesentry

# Install dependencies
pip install -r requirements.txt

# Run
sudo python3 scanner.py
```

### Option 2: System-Wide Installation
Install BlueSentry as a command-line tool accessible from anywhere.

```bash
# From within the project directory
pip install .

# Now you can run it simply by typing:
sudo bluesentry
```

*Note: On Linux, accessing the Bluetooth adapter usually requires root privileges (`sudo`).*

## Usage Guide

### 1. The Scanner
The main tool for discovering devices.

**Basic Scan (20 seconds):**
```bash
sudo bluesentry
```

**Custom Duration (e.g., 60 seconds):**
```bash
sudo bluesentry --duration 60
```

**Passive Mode (No UI, just logging):**
Ideal for background monitoring.
```bash
sudo bluesentry --passive --output night_scan.csv
```

**Command Line Arguments:**
*   `-t`, `--duration`: Scan duration in seconds (default: 20).
*   `-o`, `--output`: Custom CSV filename for the log.
*   `-p`, `--passive`: Run without the interactive menu (logs data and exits).

### 2. Post-Scan Actions
After an interactive scan finishes, you will see a menu:
1.  **Interrogate:** Select a device ID to connect and inspect its services.
2.  **BLOODHOUND:** Select a device ID to immediately launch the signal tracker.

### 3. Standalone Tools
You can also run the modules individually if you already have a target MAC address.

**Tracker:**
```bash
sudo python3 tracker.py AA:BB:CC:11:22:33
```

**Interrogator:**
```bash
sudo python3 interrogator.py AA:BB:CC:11:22:33
```

## Running Tests
To verify the internal logic (Vendor database, Apple identification, etc.):

```bash
python3 -m unittest discover tests
```

## Disclaimer
This tool is for educational and security research purposes only. Always respect privacy and applicable laws when monitoring wireless traffic.
