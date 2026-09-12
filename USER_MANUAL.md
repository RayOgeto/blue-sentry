# BlueSentry™ Production Operations & Technical Reference Manual

**Document Version:** 1.0.0  
**Target Release:** BlueSentry Enterprise & Security Research Suite  
**Classification:** Technical Documentation & Production Deployment Guide  

---

## Table of Contents
1. [System Architecture & Theoretical Foundations](#1-system-architecture--theoretical-foundations)
   * 1.1 Bluetooth Low Energy (GAP vs. GATT)
   * 1.2 Advertising Packet Anatomy & Over-the-Air Leakage
   * 1.3 Signal Physics: RSSI, Path Loss, and EMA Filtering
   * 1.4 IEEE MAC Address Privacy: Public vs. Random (RPA/NRPA)
   * 1.5 Proprietary Protocol Fingerprinting (Apple Continuity)
2. [Hardware & System Requirements](#2-hardware--system-requirements)
   * 2.1 Compatible Bluetooth Controllers & HCI Chipsets
   * 2.2 Operating System & Kernel Prerequisites
3. [Installation & Hardening](#3-installation--hardening)
   * 3.1 Standard Python Virtual Environment Setup
   * 3.2 System-Wide Package Installation
   * 3.3 Non-Root Execution via Linux Capabilities (`setcap`)
   * 3.4 Platform-Specific Setup (Ubuntu/Debian, Arch, Fedora, Raspberry Pi)
4. [Operation & Command Reference](#4-operation--command-reference)
   * 4.1 CLI Synopsis & Argument Flags
   * 4.2 Interactive Terminal Dashboard (TUI)
   * 4.3 Interpreting the Proximity Radar
   * 4.4 Device Interrogation (GATT Crawler)
   * 4.5 Bloodhound Signal Tracker
5. [24/7 Background Deployment (Systemd Sentry Node)](#5-247-background-deployment-systemd-sentry-node)
   * 5.1 Systemd Service Configuration
   * 5.2 Automated Log Rotation (`logrotate`)
   * 5.3 Ingesting Telemetry into SIEM / Pandas
6. [Data Schema & Output Format](#6-data-schema--output-format)
7. [Troubleshooting & Diagnostic Runbook](#7-troubleshooting--diagnostic-runbook)

---

## 1. System Architecture & Theoretical Foundations

BlueSentry is built upon the asynchronous event-driven Python BLE stack (`bleak`), communicating directly with the Linux BlueZ D-Bus management interface (`org.bluez`). 

```
                                  +---------------------------------------+
                                  |         BlueSentry CLI / TUI          |
                                  |  (Rich Live / Plotext / Argparse)     |
                                  +-------------------+-------------------+
                                                      |
                          +---------------------------+---------------------------+
                          |                                                       |
              +-----------v------------+                             +------------v-----------+
              |   Scanner Engine       |                             |   Bloodhound Tracker   |
              |   (Passive Listener)   |                             |   (Target Locked EMA)  |
              +-----------+------------+                             +------------+-----------+
                          |                                                       |
                          +---------------------------+---------------------------+
                                                      |
                                          +-----------v------------+
                                          | Bleak Async Core Engine|
                                          +-----------+------------+
                                                      |
                                          +-----------v------------+
                                          |   D-Bus System Bus     |
                                          |      (org.bluez)       |
                                          +-----------+------------+
                                                      |
                                          +-----------v------------+
                                          | Linux Kernel (bluetooth|
                                          |  hci_uart / btusb)     |
                                          +-----------+------------+
                                                      |
                                          +-----------v------------+
                                          | Physical Radio (HCI)   |
                                          |  2.4 GHz Antenna       |
                                          +------------------------+
```

### 1.1 Bluetooth Low Energy (GAP vs. GATT)
BLE operates in two distinct operational planes:
* **GAP (Generic Access Profile):** Controls broadcasting, discovery, and advertising. Devices broadcast unencrypted advertisement packets on three dedicated primary advertising channels: **Channel 37 (2402 MHz)**, **Channel 38 (2426 MHz)**, and **Channel 39 (2480 MHz)**. These frequencies avoid the common Wi-Fi channels (1, 6, and 11).
* **GATT (Generic Attribute Profile):** Controls connection-oriented data transfer once two devices form a pair/bond. GATT structures data hierarchically: **Profiles → Services → Characteristics → Descriptors**.

BlueSentry operates primarily as a **passive GAP observer** (zero transmission, zero radio emission) before selectively switching to **GATT client mode** when interrogating a specific target.

---

### 1.2 Advertising Packet Anatomy & Over-the-Air Leakage
A legacy BLE advertising packet has a maximum radio frame of 47 bytes, of which up to **31 bytes** constitute the Advertising Data (AD) payload. The payload is divided into Type-Length-Value (TLV) structures:

$$\text{AD Structure} = \left[ \text{Length (1 byte)} \parallel \text{AD Type (1 byte)} \parallel \text{AD Data (} n \text{ bytes)} \right]$$

Common AD Types captured by BlueSentry:
* `0x01`: Flags (e.g., General Discoverable Mode, BR/EDR Not Supported).
* `0x08` / `0x09`: Shortened or Complete Local Name (e.g., `"Ray's Watch"`).
* `0x02` / `0x03` / `0x06` / `0x07`: 16-bit, 32-bit, or 128-bit Service UUID lists.
* `0xFF`: **Manufacturer Specific Data**. The first 2 bytes denote the Bluetooth SIG Company ID (e.g., `0x004C` for Apple, `0x0006` for Microsoft), followed by arbitrary proprietary binary payloads.

---

### 1.3 Signal Physics: RSSI, Path Loss, and EMA Filtering
RSSI (Received Signal Strength Indicator) measures the power present in a received radio signal in decibels relative to one milliwatt ($\text{dBm}$).

#### The Log-Distance Path Loss Model:
Radio signal attenuation over distance follows the log-normal path loss formula:

$$\text{RSSI}(d) = -10n \log_{10}\left(\frac{d}{d_0}\right) + A + X_\sigma$$

Where:
* $d$: Physical distance between transmitter and receiver.
* $d_0$: Reference distance (typically $1.0\text{ m}$).
* $A$: Received signal power at $1\text{ meter}$ (typically $-55\text{ to } -65\text{ dBm}$).
* $n$: Path loss exponent ($2.0$ in free space; $2.7 - 4.5$ in obstructed indoor environments).
* $X_\sigma$: Zero-mean Gaussian random variable representing multipath reflections, constructive/destructive interference, and human body shadowing.

#### Exponential Moving Average (EMA) Smoothing:
Because indoor multipath interference causes instant $\pm 15\text{ dBm}$ spikes, raw RSSI readings are unstable. BlueSentry's Bloodhound Tracker runs an Exponential Moving Average filter across successive advertising packets:

$$S_t = \alpha \cdot \text{RSSI}_t + (1 - \alpha) \cdot S_{t-1}$$

Where $\alpha = 0.35$ provides an optimal balance between responsiveness (decaying stale readings) and noise attenuation.

---

### 1.4 IEEE MAC Address Privacy: Public vs. Random (RPA/NRPA)
A standard Bluetooth Device Address (BD_ADDR) is 48 bits (6 bytes), formatted identically to an Ethernet MAC address (`XX:XX:XX:XX:XX:XX`).

BlueSentry analyzes the most significant byte (MSB) to classify the privacy state:

```
 MSB Byte: [ b7 | b6 | b5 | b4 | b3 | b2 | b1 | b0 ]
                                            ^
                                     Bit 1 (U/L Bit)
                                     0 = Universally Administered (PUBLIC)
                                     1 = Locally Administered (RANDOM)
```

If **Bit 1 is 0**, the address is **Public (Static)**. It is registered with the IEEE OUI database, globally unique, permanently tied to the device hardware, and easily trackable across locations.

If **Bit 1 is 1**, the address is **Random (Private)**. BlueSentry further decodes bits 7 and 6:
* `11` ($0\text{xC0}$): **Static Random Address** (constant per boot cycle).
* `01` ($0\text{x40}$): **Resolvable Private Address (RPA)** (rotates every 15 minutes; generated using an Identity Resolving Key / AES-128 cryptographic hash).
* `00` ($0\text{x00}$): **Non-Resolvable Private Address (NRPA)** (completely random, rarely used except by beacons).

---

### 1.5 Proprietary Protocol Fingerprinting (Apple Continuity)
Even when an Apple device obscures its name and rotates its MAC address, it continually broadcasts `AD Type 0xFF` with Company ID `0x004C`. The payload starts with an Apple Continuity Sub-type byte:

| Type Byte | Protocol / Feature | Forensic / Recon Value |
| :--- | :--- | :--- |
| `0x02` | **iBeacon** | Proximity tag broadcasting Proximity UUID, Major, Minor, and TX Power. |
| `0x05` | **AirDrop** | Indicates user is opening the share sheet or scanning for nearby contacts. |
| `0x07` | **AirPods** | Broadcasts battery levels for left earbud, right earbud, and case. |
| `0x08` / `0x09`| **AirPlay** | Video/audio casting target detection. |
| `0x0C` | **Handoff** | Leaks active cross-device clipboards and continuity clipboard tasks. |
| `0x10` | **Nearby Action**| Broadcast when Apple Watch unlocks Mac, or during Setup Assistants. |
| `0x12` | **Find My (AirTag)** | Offline device location mesh broadcast. Unregistered tags leak tracking telemetry. |

---

## 2. Hardware & System Requirements

### 2.1 Compatible Bluetooth Controllers & HCI Chipsets
BlueSentry interfaces through the Linux Host Controller Interface (HCI). Supported chips:
* **Intel:** Dual Band Wireless-AC / Wi-Fi 6 & 6E series (AX200, AX201, AX210, BE200).
* **Broadcom / Cypress:** BCM43438, BCM43455 (onboard Raspberry Pi 3B+, 4B, 5, Zero 2 W).
* **Realtek:** RTL8761B, RTL8821CE, RTL8852AE USB dongles.
* **Cambridge Silicon Radio (CSR):** CSR8510 A10 based USB dongles (Bluetooth 4.0).

### 2.2 Operating System & Kernel Prerequisites
* **Linux Kernel:** $\ge 5.4$ with `CONFIG_BT`, `CONFIG_BT_RFCOMM`, and `CONFIG_BT_HCIBTUSB` enabled.
* **BlueZ Stack:** $\ge 5.50$ (BlueZ 5.64+ recommended for modern LE 2M PHY support).
* **Python Runtime:** Python 3.8 through Python 3.14.

---

## 3. Installation & Hardening

### 3.1 Standard Python Virtual Environment Setup
```bash
# Update package repositories and install BlueZ system packages
sudo apt update && sudo apt install -y bluez bluez-tools python3 python3-pip python3-venv rfkill

# Clone the repository
git clone https://github.com/RayOgeto/blue-sentry.git
cd blue-sentry

# Initialize isolated virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Upgrade packaging tools and install BlueSentry
pip install --upgrade pip
pip install -r requirements.txt
```

---

### 3.2 System-Wide Package Installation
To install the `bluesentry` binary system-wide:
```bash
# From within the repository directory
pip install .

# Verify the CLI tool entry point
bluesentry --help
```

---

### 3.3 Non-Root Execution via Linux Capabilities (`setcap`)
> [!IMPORTANT]
> Running network tools with `sudo` exposes your entire system to risks if third-party dependencies are compromised. **Do not run BlueSentry as root.** Instead, grant network capture capabilities directly to the Python binary.

Execute the following hardening sequence:
```bash
# 1. Locate the absolute path of your Python binary
PY_PATH=$(readlink -f $(which python3))
echo "Hardening Python at: $PY_PATH"

# 2. Grant raw network and admin capabilities
sudo setcap 'cap_net_raw,cap_net_admin+eip' "$PY_PATH"

# 3. Add your standard user to the bluetooth system group
sudo usermod -aG bluetooth $USER

# 4. Refresh group permissions (or log out and log back in)
newgrp bluetooth

# 5. Now run bluesentry completely without sudo!
bluesentry --duration 10
```

---

### 3.4 Platform-Specific Setup

#### Debian / Ubuntu / Mint / Kali
```bash
sudo apt install -y bluez libglib2.0-dev
sudo rfkill unblock bluetooth
sudo systemctl enable --now bluetooth
```

#### Arch Linux / Manjaro
```bash
sudo pacman -S bluez bluez-utils python-pip
sudo rfkill unblock bluetooth
sudo systemctl enable --now bluetooth
```

#### Fedora / RHEL / AlmaLinux
```bash
sudo dnf install -y bluez bluez-libs python3-devel
sudo rfkill unblock bluetooth
sudo systemctl enable --now bluetooth
```

#### Raspberry Pi OS (Headless Appliance)
```bash
sudo apt update && sudo apt install -y bluez python3-venv
# Ensure onboard Bluetooth firmware is loaded
sudo systemctl restart hciuart
```

---

## 4. Operation & Command Reference

### 4.1 CLI Synopsis & Argument Flags
```text
bluesentry [-h] [-t DURATION] [-o OUTPUT] [-p]
```

#### Options:
| Flag | Long Argument | Type | Default | Description |
| :--- | :--- | :--- | :--- | :--- |
| `-t` | `--duration` | Integer | `20` | Total duration of the scanning phase in seconds. |
| `-o` | `--output` | String | `None` | Path to save the output CSV log. If omitted, automatically writes to `sentry_log_YYYYMMDD_HHMMSS.csv`. |
| `-p` | `--passive` | Flag | `False` | Enables headless surveillance mode. Suppresses the interactive TUI and post-scan menu; writes directly to disk. |
| `-h` | `--help` | Flag | — | Displays the full help documentation and operational examples. |

---

### 4.2 Interactive Terminal Dashboard (TUI)
When launched interactively (`bluesentry --duration 30`), the screen splits into two synchronized operational zones:

1. **Top Pane — Live Feed Table:**
   * **ID:** Sequential index of discovered devices, dynamically ranked by RSSI signal strength (strongest at top).
   * **Address:** Hardware BD_ADDR or OS-provided identifier.
   * **Type:** Privacy classification:
     * `[green]RAND[/green]`: Device uses a randomized MAC address (anti-tracking enabled).
     * `[red]PUB[/red]`: Device uses a static, public IEEE-assigned MAC address (trackable across sessions).
     * `[dim]UNK[/dim]`: Non-standard or masked identifier (e.g. macOS UUID).
   * **RSSI:** Signal power in dBm, color-coded (`> -60 dBm` in green, `-60 to -80 dBm` in yellow, `< -80 dBm` in red).
   * **Name / Manufacturer:** Resolved local broadcast name alongside decoded manufacturer or Apple Continuity protocol tag.
   * **Services / Tags:** Identified GATT service profiles (e.g. `Heart Rate`, `Battery`, `HID`, `Fast Pair`, `COVID`).

---

### 4.3 Interpreting the Proximity Radar
The bottom pane renders an ASCII radial radar grid:

```text
               |               
               |   1           
        2      |               
               |               
---------------+---------------
               |        3      
               |               
               |               
```

#### Technical Radar Properties:
* **Center Marker (`@`):** Represents your host receiver antenna.
* **Radial Distance ($r$):** Corresponds strictly to the **signal power attenuation factor**:
  $$r \propto \frac{\text{RSSI} + 30}{-70}$$
  A marker positioned near the center indicates a high RSSI ($\ge -40\text{ dBm}$, less than 1 meter). A marker placed near the perimeter indicates weak reception ($\le -90\text{ dBm}$, limit of radio range).
* **Azimuth Angle ($\theta$):** Synthetic geometric dispersion used to prevent visual marker overlapping on a 2D terminal grid. 
  *(Note: Standard single-antenna Bluetooth chips cannot calculate Angle of Arrival without a multi-element phased antenna array).*

---

### 4.4 Device Interrogation (GATT Crawler)
Selecting **Option 1** from the post-scan menu or invoking `python3 interrogator.py <MAC_ADDRESS>` launches deep GATT enumeration:

```bash
python3 interrogator.py 48:F4:7B:D4:98:8D
```

#### Interrogation Procedure:
1. **Connection Phase:** Establishes an asynchronous connection with a 12-second timeout window.
2. **Service Discovery:** Enumerates the primary and secondary GATT Service UUIDs.
3. **Characteristic Exploration:** Inspects all characteristics, their read/write/notify flags, and permissions.
4. **Data Leakage Extraction:** Reads exposed public data without requiring pairing:
   * `0x2A00`: Device Name
   * `0x2A19`: Battery Level (%)
   * `0x2A24`: Model Number String
   * `0x2A26`: Firmware Revision
   * `0x2A29`: Manufacturer Name String

---

### 4.5 Bloodhound Signal Tracker
Selecting **Option 2** from the post-scan menu or invoking `python3 tracker.py <MAC_ADDRESS>` launches targeted real-time signal tracking:

```bash
python3 tracker.py AA:BB:CC:11:22:33
```

```text
       Signal Strength: TargetBeacon [AA:BB:CC:11:22:33]
  -30 |                                                 
      |                                                 
  -50 |                          .--.                   
      |             .----.      /    \       .          
  -70 |            /      \    /      \     / \         
      |    .------'        `--'        `---'   \        
 -100 |---'                                     `-------
      +-------------------------------------------------
        Sample Time (Green = EMA Smoothed, Yellow = Raw)
```

#### Proximity Zones:
* **`!!! VERY CLOSE (< 1m) !!!`** ($\ge -52\text{ dBm}$): Target is directly adjacent to the antenna.
* **`NEARBY (1m - 3m)`** ($-53\text{ to } -70\text{ dBm}$): Target is in the same room.
* **`IN RANGE (3m - 10m)`** ($-71\text{ to } -88\text{ dBm}$): Target is detectable through light obstacles/walls.
* **`WEAK / LOST`** ($< -88\text{ dBm}$ or $> 3.5\text{ seconds}$ without an advertisement): Target is out of range or powered off.

---

## 5. 24/7 Background Deployment (Systemd Sentry Node)

Transform any Linux host or Raspberry Pi into an automated, permanent BLE surveillance sentry.

### 5.1 Systemd Service Configuration
Create the service unit file:
```bash
sudo tee /etc/systemd/system/bluesentry.service > /dev/null <<'EOF'
[Unit]
Description=BlueSentry Passive BLE Surveillance Daemon
After=bluetooth.target network.target
Requires=bluetooth.target

[Service]
Type=simple
User=ray
WorkingDirectory=/home/ray/Desktop/bt/bluesentry
ExecStart=/home/ray/Desktop/bt/bluesentry/.venv/bin/python3 scanner.py --passive --duration 86400 --output /var/log/bluesentry/daily_sentry.csv
Restart=always
RestartSec=10
AmbientCapabilities=CAP_NET_RAW CAP_NET_ADMIN

[Install]
WantedBy=multi-user.target
EOF
```

Create the log directory and activate the daemon:
```bash
sudo mkdir -p /var/log/bluesentry
sudo chown -R ray:ray /var/log/bluesentry

sudo systemctl daemon-reload
sudo systemctl enable --now bluesentry.service
sudo systemctl status bluesentry.service
```

---

### 5.2 Automated Log Rotation (`logrotate`)
Configure automatic daily compression and retention:
```bash
sudo tee /etc/logrotate.d/bluesentry > /dev/null <<'EOF'
/var/log/bluesentry/*.csv {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 0640 ray ray
}
EOF
```

---

### 5.3 Ingesting Telemetry into SIEM / Pandas
Analyze exported CSV logs programmatically:

```python
import pandas as pd

# Load log into DataFrame
df = pd.read_csv("sentry_log_20260912_230000.csv")

# Filter for public (trackable) devices with strong signals
trackable = df[(df["Is Randomized"] == "No") & (df["Last RSSI"] > -70)]

# Group by vendor
vendor_summary = df["Manufacturer"].value_counts()
print(vendor_summary)
```

---

## 6. Data Schema & Output Format

Every BlueSentry session saves a sanitized, pure CSV file. The columns and types are strictly standardized:

| Column Name | Data Type | Nullable | Description / Example |
| :--- | :--- | :--- | :--- |
| `Address` | String (MAC/UUID) | No | Target BD_ADDR (`48:F4:7B:D4:98:8D`) or OS UUID. |
| `Name` | String | No | Local broadcast name or `"Unknown"`. |
| `Manufacturer` | String | No | Resolved vendor (`"Apple AirDrop"`, `"Fitbit, Inc."`). |
| `Last RSSI` | Integer | No | Last observed radio signal strength in dBm (`-65`). |
| `Services` | String (Semicolon) | Yes | Semicolon-delimited recognized services (`Heart Rate; Battery Service`). |
| `Address Type`| String | No | `"Public (Trackable)"`, `"Resolvable Private (RPA)"`, or `"Static Random"`. |
| `Is Randomized`| String (Yes/No) | No | `"Yes"`, `"No"`, or `"Unknown"`. |
| `First Seen` | String (HH:MM:SS) | No | Timestamp of first detected advertisement frame. |
| `Last Seen` | String (HH:MM:SS) | No | Timestamp of most recent advertisement frame. |

---

## 7. Troubleshooting & Diagnostic Runbook

### Issue 1: `Bluetooth adapter not found` or `BleakError: org.bluez.Error.NotReady`
**Root Cause:** Bluetooth adapter is unpowered, blocked by the Linux rfkill subsystem, or the BlueZ daemon is stopped.  
**Resolution:**
```bash
# 1. Inspect rfkill software/hardware switches
rfkill list bluetooth

# 2. Unblock if blocked
sudo rfkill unblock bluetooth

# 3. Bring the HCI device up
sudo hciconfig hci0 up

# 4. Restart the system BlueZ daemon
sudo systemctl restart bluetooth
```

---

### Issue 2: `Permission Denied` during raw BLE scanning
**Root Cause:** Python is running without `CAP_NET_RAW` / `CAP_NET_ADMIN` capabilities and without `sudo`.  
**Resolution:**
```bash
sudo setcap 'cap_net_raw,cap_net_admin+eip' $(readlink -f $(which python3))
```

---

### Issue 3: Device fails to interrogate (`Connection timed out after 12 seconds`)
**Root Cause:**
1. The target peripheral is a **Non-Connectable Advertiser** (e.g., standard iBeacon or Eddystone broadcaster).
2. The peripheral has moved out of radio range ($< -90\text{ dBm}$).
3. The peripheral is already connected to another host (BLE single-connection limitation).  
**Resolution:** Verify proximity using Bloodhound (`tracker.py`) before initiating interrogation. Connectable devices will show in the live feed with connection flags.

---

### Issue 4: Address Classification reports `UNK`
**Root Cause:** Running on macOS where CoreBluetooth abstracts the physical BD_ADDR into a system UUID.  
**Resolution:** Use Linux (Ubuntu, Debian, Raspberry Pi OS) for full hardware MAC access and IEEE address classification.

---

*Manual maintained by BlueSentry Systems Engineering Team.*
