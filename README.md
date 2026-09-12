# BlueSentry™

**Advanced Bluetooth Low Energy (BLE) Surveillance, Forensics & Proximity Tracking Suite**

[![Status](https://img.shields.io/badge/Status-Production%20Ready-brightgreen.svg)](#)
[![Python Version](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](#)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](#)
[![Manual](https://img.shields.io/badge/Docs-Enterprise%20Manual-orange.svg)](USER_MANUAL.md)
[![Man Page](https://img.shields.io/badge/Man%20Page-bluesentry(1)-lightgrey.svg)](docs/bluesentry.1)

**BlueSentry** is a high-performance, passive Bluetooth Low Energy (BLE) reconnaissance, auditing, and telemetry engine. Operating directly on top of the Linux BlueZ D-Bus layer, it captures and analyzes over-the-air GAP advertising broadcasts without establishing connections, pair requests, or emitting radio transmissions.

The suite de-anonymizes proprietary vendor frames (including Apple Continuity, AirDrop, and Find My networks), classifies IEEE 802 MAC address privacy schemes, performs deep GATT attribute interrogation, and physically locates targets using an Exponential Moving Average (EMA) stabilized RSSI tracking radar.

---

## 📖 Documentation & Technical References

* 📘 **[Production Operations & Technical Reference Manual (USER_MANUAL.md)](USER_MANUAL.md)**: Deep dive into BLE GAP/GATT architecture, radio path loss physics, 24/7 systemd sentry deployment, and SIEM ingestion.
* 📄 **[Unix Man Page (`docs/bluesentry.1`)](docs/bluesentry.1)**: Formal system manual formatted in standard troff/groff format (`man -l docs/bluesentry.1`).
* 🌐 **[Interactive Web Documentation (`docs/index.html`)](docs/index.html)**: Browser-based visual terminal demonstration and guide.

---

## ⚡ Key Capabilities

```
+---------------------------------------------------------------------------------+
|                                BLUESENTRY SUITE                                 |
+------------------------------------+--------------------------------------------+
| 📡 Passive BLE Scanner             | 🐕 Bloodhound Signal Tracker               |
| - Zero-transmission GAP monitoring | - Targeted BD_ADDR signal lock             |
| - Real-time RSSI-proximity radar   | - EMA noise-filtering (alpha = 0.35)       |
| - IEEE MAC randomization detection | - Live plotext terminal trend graphing     |
+------------------------------------+--------------------------------------------+
| 🔬 GATT Attribute Interrogator     | 🛡️ Security Hardening & 24/7 Sentry         |
| - Full GATT hierarchy tree dump    | - Native Linux capabilities (non-root)     |
| - Readable characteristic crawler  | - Systemd service & logrotate daemon       |
| - Safe connection timeouts (12s)   | - Clean CSV telemetry logging (no ANSI)    |
+------------------------------------+--------------------------------------------+
```

---

## 🚀 Quick Start

### 1. Installation

```bash
# Clone the repository
git clone https://github.com/RayOgeto/blue-sentry.git
cd blue-sentry

# Create and activate an isolated virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# (Optional) Install globally as a CLI command
pip install .
```

### 2. Hardening (Non-Root Execution via `setcap`)

> [!TIP]
> In production and lab environments, **do not run BlueSentry with `sudo`**. Grant raw network socket capabilities directly to your Python binary:

```bash
# Grant Linux network capabilities
sudo setcap 'cap_net_raw,cap_net_admin+eip' $(readlink -f $(which python3))

# Add user to bluetooth group
sudo usermod -aG bluetooth $USER
newgrp bluetooth
```

### 3. Usage Examples

#### Run Live Interactive Surveillance (20 seconds):
```bash
bluesentry
```

#### Headless 24/7 Monitoring (Surveillance Daemon):
```bash
bluesentry --passive --duration 86400 --output /var/log/bluesentry/overnight.csv
```

#### Target Track a Specific Device (Bloodhound):
```bash
python3 tracker.py AA:BB:CC:11:22:33
```

#### Interrogate Exposed GATT Services:
```bash
python3 interrogator.py AA:BB:CC:11:22:33
```

---

## 📋 Command Line Interface

```text
usage: bluesentry [-h] [-t DURATION] [-o OUTPUT] [-p]

BlueSentry: Advanced BLE Scanner, Analyzer & Tracker

options:
  -h, --help            show this help message and exit
  -t, --duration DURATION
                        Scan duration in seconds (default: 20)
  -o, --output OUTPUT   Output CSV filename (default: sentry_log_TIMESTAMP.csv)
  -p, --passive         Run in passive headless mode (no TUI, just log)
```

---

## 📊 Output Data Schema

Every session automatically records telemetry to a clean, pure CSV file formatted for direct ingestion into SIEM platforms or Pandas:

| Column Name | Type | Description |
| :--- | :--- | :--- |
| `Address` | String | Hardware BD_ADDR or OS UUID identifier. |
| `Name` | String | Broadcasted local device name or `"Unknown"`. |
| `Manufacturer` | String | Identified vendor or Apple Continuity protocol tag. |
| `Last RSSI` | Integer | Last received signal power in dBm. |
| `Services` | String | Recognized GATT Service names separated by semicolons. |
| `Address Type` | String | `"Public (Trackable)"`, `"Resolvable Private (RPA)"`, etc. |
| `Is Randomized`| String | `"Yes"` (privacy active), `"No"` (static/trackable), or `"Unknown"`.|
| `First Seen` | String | Session timestamp when device was first captured (`HH:MM:SS`). |
| `Last Seen` | String | Timestamp of most recently received advertisement frame. |

---

## 🧪 Verification & Testing

Verify internal vendor resolution, packet parsers, and EMA smoothing:
```bash
python3 -m unittest discover tests -v
```

View the system manual page:
```bash
man -l docs/bluesentry.1
```

---

## ⚖️ License & Ethical Use

Distributed under the MIT License. Designed for authorized security assessments, network defense, and academic research. Users are responsible for complying with applicable local radio spectrum and privacy regulations.
