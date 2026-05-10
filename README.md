# BlueSentry 🔵

<div align="center">

[![Python](https://img.shields.io/badge/Python-100%25-3776ab?logo=python&logoColor=white)](#)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](#license)
[![Platform](https://img.shields.io/badge/Platform-Linux%20%7C%20macOS-blue)](#)
[![Status](https://img.shields.io/badge/Status-Production--Ready-brightgreen)](#)

**Advanced Bluetooth Low Energy (BLE) scanner, analyzer, and tracker for device discovery and location.**

[📖 Documentation](./docs) • [🐛 Report Bug](https://github.com/RayOgeto/blue-sentry/issues) • [💡 Request Feature](https://github.com/RayOgeto/blue-sentry/issues)

</div>

---

## 📋 Overview

**BlueSentry** is a sophisticated, production-ready BLE scanning and analysis tool that goes far beyond simple device discovery. It features real-time radar visualization, privacy analysis, brand identification, signal tracking, and deep device inspection capabilities.

Perfect for security researchers, developers, network administrators, and anyone needing comprehensive Bluetooth device monitoring and analysis.

---

## ⚠️ Legal & Ethical Notice

**Important:** This tool is designed for **educational and authorized security research only.**

- ✅ Use on YOUR devices and networks
- ✅ Use for authorized security audits
- ✅ Use for network research
- ❌ Do NOT use without permission
- ❌ Do NOT track people without consent
- ❌ Do NOT use for surveillance

**Always comply with local laws and regulations.** Unauthorized access to computer systems is illegal.

---

## ✨ Features

### 🔍 Advanced Scanner (`bluesentry`)

**Live Radar Visualization**
- Real-time text-based radar display
- Shows nearby devices relative to position
- Based on signal strength (RSSI)
- Distance estimation
- Visual device indicators

**Privacy Analysis**
- Detects randomized MAC addresses
- Identifies public/trackable addresses
- Privacy risk assessment
- De-anonymization capabilities
- Privacy recommendations

**Brand Identification**
- Identifies Apple devices (AirTags, AirPods, AirDrop)
- Recognizes Fitbit, Tile, Garmin devices
- Detects major manufacturers
- Works even without broadcast names
- MAC OUI database lookup

**Sentry Mode (Auto-Logging)**
- Automatic CSV logging of all scans
- Crash-safe data persistence
- Timestamped records
- No manual intervention needed
- Easy data analysis

**Advanced Filtering**
- Filter by device type
- Filter by signal strength
- Filter by manufacturer
- Real-time filtering
- Search capabilities

### 🎯 Bloodhound Tracker

**Signal Tracking**
- "Hot/Cold" game for physical location
- Real-time signal strength monitoring
- Moving target support
- Accuracy indicators
- Distance estimation

**Graphing**
- Live RSSI graph display
- Signal trend visualization
- Strength history
- Multiple target tracking
- Export graphs

**Proximity Alerts**
- Visual alerts when very close
- "Getting warmer/colder" feedback
- Customizable thresholds
- Audio alerts (optional)
- Vibration feedback (mobile)

**Target Management**
- Lock on to specific devices
- Switch targets easily
- Tracking history
- Target statistics
- Performance metrics

### 🔬 Interrogator (Deep Inspection)

**GATT Service Inspection**
- Dump full GATT service table
- Characteristic discovery
- Descriptor enumeration
- Property analysis
- Permission detection

**Data Leak Detection**
- Reads standard characteristics
- Finds exposed data
- Battery level extraction
- Device name extraction
- Firmware version detection
- Manufacturer data reading

**Security Assessment**
- Identifies unencrypted data
- Checks for weak authentication
- Detects security gaps
- Risk scoring
- Recommendations

**Custom Commands**
- Read any characteristic
- Write to characteristics
- Subscribe to notifications
- Custom protocol support
- Hex data handling

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| **Language** | Python 3.7+ |
| **BLE Library** | Bleak |
| **Database** | SQLite |
| **CLI** | Click / Typer |
| **Data Format** | CSV, JSON |
| **OS Support** | Linux, macOS |
| **License** | MIT |

---

## 📋 Requirements

### System Requirements

| Component | Requirement |
|-----------|------------|
| **Python** | 3.7 or higher |
| **OS** | Linux or macOS |
| **Bluetooth** | Hardware with BLE support |
| **Permissions** | Root/Admin (for BLE access) |
| **Dependencies** | See requirements.txt |

### Platform Support

- **Linux** ✅ Full support (BlueZ required)
- **macOS** ✅ Full support
- **Windows** ⚠️ Limited (Bleak supports it, but CLI optimized for Unix)

### Linux Prerequisites

```bash
# Ubuntu/Debian
sudo apt-get install bluez python3-dev libglib2.0-dev

# Fedora
sudo dnf install bluez python3-devel glib2-devel

# Arch
sudo pacman -S bluez python
```

---

## 🚀 Installation

### Option 1: Quick Run (No System Installation)

```bash
# Clone the repository
git clone https://github.com/RayOgeto/blue-sentry.git
cd blue-sentry

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the scanner
sudo python3 scanner.py
```

### Option 2: System-Wide Installation

```bash
# From project directory
pip install .

# Now you can run from anywhere
sudo bluesentry
```

### Option 3: Using Docker

```bash
# Build image
docker build -t bluesentry .

# Run with Bluetooth access
docker run --privileged -it bluesentry bluesentry
```

### Option 4: Poetry

```bash
# Install dependencies
poetry install

# Run
poetry run python scanner.py
```

---

## 📖 Usage Guide

### 1. The Scanner (Main Tool)

**Basic Scan (20 seconds default):**
```bash
sudo bluesentry
```

**Custom Duration (60 seconds):**
```bash
sudo bluesentry --duration 60
```

**Passive Mode (No UI, just logging):**
```bash
sudo bluesentry --passive --output night_scan.csv
```

**Verbose Output:**
```bash
sudo bluesentry --verbose
```

**Multiple Scans:**
```bash
sudo bluesentry --repeat 5 --interval 10
```

#### Command Line Arguments

| Argument | Short | Type | Default | Description |
|----------|-------|------|---------|-------------|
| `--duration` | `-t` | int | 20 | Scan duration in seconds |
| `--output` | `-o` | str | auto | CSV filename for log |
| `--passive` | `-p` | flag | false | Run without interactive menu |
| `--verbose` | `-v` | flag | false | Verbose output |
| `--repeat` | `-r` | int | 1 | Number of scans |
| `--interval` | `-i` | int | 5 | Interval between scans (seconds) |
| `--filter` | `-f` | str | none | Filter by device type |
| `--rssi-min` | | int | -100 | Minimum signal strength |

#### Scanner Output

```
╔═══════════════════════════════════════════════════════════╗
║                    BLUESENTRY RADAR                      ║
╠═══════════════════════════════════════════════════════════╣
║                                                           ║
║              Device Scan Results (20s)                   ║
║                                                           ║
║  Devices Found: 5                                        ║
║                                                           ║
║  [00:00:A4:00:00:00] - Apple AirPod Pro                 ║
║  Signal: ████████░░ (-45 dBm) ~2.5m                    ║
║  MAC: Public (Trackable)                                ║
║                                                           ║
║  [4C:EF:9F:12:34:56] - Apple iPhone                      ║
║  Signal: ██████░░░░ (-65 dBm) ~5m                       ║
║  MAC: Randomized (Private)                              ║
║                                                           ║
║  [E3:AA:9F:12:34:56] - Unknown Device                    ║
║  Signal: ███░░░░░░░ (-75 dBm) ~8m                       ║
║  MAC: Randomized (Private)                              ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
```

### 2. Post-Scan Actions

After an interactive scan completes, you'll see a menu:

```
What would you like to do?

1. [I] Interrogate - Connect to a device and inspect services
2. [B] BLOODHOUND - Launch signal tracker for a device
3. [L] List Results - View detailed results
4. [E] Export Data - Export to JSON/CSV
5. [Q] Quit

Enter choice (I/B/L/E/Q):
```

**Option 1 - Interrogate:**
```
Enter device ID to interrogate: 1
Connecting to 00:00:A4:00:00:00...
Connected!

GATT Services:
- Generic Access (1800)
  - Device Name: "Apple AirPod Pro"
  - Appearance: 1313
  
- Generic Attribute (1801)

- Device Information (180A)
  - Manufacturer Name: Apple Inc.
  - Model Number: A2968
  - Serial Number: [REDACTED]
  - Hardware Revision: A
  
- Battery Service (180F)
  - Battery Level: 85%
  - Battery Status: Charging

Device Status: Standard Apple AirPod Pro
Security: No encryption detected
Recommendations:
  ✓ Keep firmware updated
  ✓ Disable Bluetooth when not in use
  ✓ Review privacy settings in iOS
```

**Option 2 - BLOODHOUND:**
```
Enter device ID to track: 1
Target: 00:00:A4:00:00:00 (Apple AirPod Pro)

Live Signal Tracking
═══════════════════════════════════════════

Current: -62 dBm (~3m)      ▓▓▓▓▓░░░░░

Time    Signal    Distance   Status
─────────────────────────────────────
00:15   -62 dBm   3.0m       🟢 Getting Closer!
00:30   -65 dBm   4.5m       🟡 Getting Farther
01:00   -58 dBm   2.5m       🟢 Very Close!
01:30   -70 dBm   6m         🔴 Losing Signal

[Press Ctrl+C to stop tracking]
```

### 3. Standalone Tools

Run modules directly without the main menu:

**Tracker (Signal Following):**
```bash
sudo python3 tracker.py AA:BB:CC:11:22:33
```

**Interrogator (Device Inspection):**
```bash
sudo python3 interrogator.py AA:BB:CC:11:22:33
```

**Passive Scanner (Background Logging):**
```bash
sudo python3 scanner.py --passive --output devices.csv --repeat 0
```

---

## 🔬 Advanced Usage

### Scripting

**Python Script Example:**
```python
from bluesentry import BLEScanner, Interrogator, Tracker

# Scan for devices
scanner = BLEScanner(duration=30)
devices = scanner.scan()

# Filter Apple devices
apple_devices = [d for d in devices if 'Apple' in d.manufacturer]

# Interrogate first Apple device
if apple_devices:
    target = apple_devices[0]
    interrogator = Interrogator(target.address)
    services = interrogator.get_gatt_services()
    print(services)

# Track a device
tracker = Tracker(target.address, duration=60)
tracker.track()
```

### Scheduled Scanning

```bash
# Scan every hour using cron
0 * * * * cd /home/user/bluesentry && sudo python3 scanner.py --passive --output logs/scan_$(date +\%s).csv
```

### Continuous Monitoring

```bash
# Monitor for 24 hours with results every hour
sudo bluesentry --repeat 24 --interval 3600 --passive --output monitoring.csv
```

### Export & Analysis

```bash
# Export results as JSON
sudo python3 scanner.py --output results.csv
python3 scripts/csv_to_json.py results.csv

# Analyze data
python3 scripts/analyze_devices.py results.json

# Generate report
python3 scripts/generate_report.py results.json report.html
```

---

## 📊 Data Formats

### CSV Export

```csv
timestamp,address,name,rssi,manufacturer,privacy_type,distance_m
2026-05-10T15:30:00Z,00:00:A4:00:00:00,Apple AirPod Pro,-45,Apple,public,2.5
2026-05-10T15:30:01Z,4C:EF:9F:12:34:56,Apple iPhone,-65,Apple,randomized,5.0
```

### JSON Export

```json
{
  "scan_timestamp": "2026-05-10T15:30:00Z",
  "scan_duration_seconds": 20,
  "devices_found": 2,
  "devices": [
    {
      "address": "00:00:A4:00:00:00",
      "name": "Apple AirPod Pro",
      "rssi": -45,
      "estimated_distance_m": 2.5,
      "manufacturer": "Apple",
      "mac_privacy": "public",
      "services": [1800, 180F],
      "last_seen": "2026-05-10T15:30:05Z"
    }
  ]
}
```

---

## 🧪 Testing

### Run Tests

```bash
# Unit tests
python -m pytest tests/unit -v

# Integration tests
python -m pytest tests/integration -v

# Test coverage
python -m pytest --cov=bluesentry tests/
```

### Test Examples

```bash
# Test scanner with mock devices
python -m pytest tests/test_scanner.py -v

# Test interrogator
python -m pytest tests/test_interrogator.py -v

# Test brand identification
python -m pytest tests/test_identification.py -v
```

---

## 🔐 Security Considerations

### Privacy Risks
- ⚠️ Some devices use **public MAC addresses** (trackable)
- ⚠️ Device names may reveal **identity information**
- ⚠️ Manufacturer data can be **personally identifying**
- ⚠️ GATT services may expose **sensitive information**

### Protection Measures
- ✅ Use MAC randomization in your devices
- ✅ Keep Bluetooth off when not needed
- ✅ Disable device naming features
- ✅ Review privacy settings regularly
- ✅ Update firmware promptly

### Tool Security
- Run with minimal necessary privileges
- Verify Bluetooth hardware is trusted
- Use on secure networks only
- Don't share captured data lightly

---

## 📊 Performance

| Metric | Value |
|--------|-------|
| **Scan Time** | 20-60 seconds per scan |
| **Memory Usage** | ~15-30MB |
| **CPU Usage** | Varies by number of devices |
| **Range** | Up to 100m (depends on device) |
| **Device Accuracy** | ±3 meters (signal-based) |
| **Max Devices** | Depends on density (typically 50+) |

---

## 🐛 Troubleshooting

### Bluetooth Not Found

```bash
# Check Bluetooth adapter
hciconfig

# Enable Bluetooth service
sudo systemctl start bluetooth

# Check device list
hcitool dev

# Reset adapter if frozen
sudo hciconfig hci0 reset
```

### Permission Denied

```bash
# Run with sudo
sudo bluesentry

# Or add user to bluetooth group
sudo usermod -a -G bluetooth $USER
sudo usermod -a -G dialout $USER
# Log out and log back in
```

### No Devices Detected

```bash
# Check if Bluetooth is on
hciconfig

# Try increased scan time
sudo bluesentry --duration 60

# Check signal filter
sudo bluesentry --rssi-min -100
```

### Connection Failures

```bash
# Check device is still in range
sudo hcitool lescan

# Try interrogating nearby device
sudo python3 interrogator.py AA:BB:CC:DD:EE:FF

# Reset Bluetooth
sudo hciconfig hci0 reset
```

---

## 📝 License

Licensed under the **MIT License** - see [LICENSE](LICENSE) for details.

---

## 📞 Support

- 🐛 [Report Issues](https://github.com/RayOgeto/blue-sentry/issues)
- 💬 [Discussions](https://github.com/RayOgeto/blue-sentry/discussions)
- 📧 Email: rayogetowhat@gmail.com

---

## 🙏 Acknowledgments

- Bleak library for BLE support
- BlueZ for Bluetooth stack
- Security research community
- Open-source contributors

---

## 📚 Additional Resources

- [Bluetooth Specification](https://www.bluetooth.com/specifications/)
- [Bleak Documentation](https://bleak.readthedocs.io/)
- [BLE Security](https://www.bluetooth.com/blog/bluetooth-security-privacy/)
- [OWASP IoT Security](https://owasp.org/www-project-iot-top-10/)

---

**Last Updated:** 2026-01-30  
**Status:** 🟢 Production-Ready  
**Python:** 3.7+  
**License:** MIT  
**Target Users:** Security Researchers, Developers, Network Admins
