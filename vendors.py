"""
BlueSentry Vendor & Protocol Database
Contains mappings for Bluetooth SIG Company Identifiers, Service UUIDs,
and Apple Continuity Protocol heuristics.
"""

# Bluetooth Company Identifiers
# Source: https://www.bluetooth.com/specifications/assigned-numbers/company-identifiers/
COMPANY_IDS = {
    0: "Ericsson",
    1: "Nokia Mobile Phones",
    2: "Intel Corp.",
    3: "IBM Corp.",
    4: "Toshiba Corp.",
    5: "3Com",
    6: "Microsoft",
    7: "Lucent",
    8: "Motorola",
    9: "Infineon Technologies",
    10: "Cambridge Silicon Radio",
    11: "Silicon Wave",
    12: "Digianswer A/S",
    13: "Texas Instruments",
    15: "Broadcom",
    19: "Atmel",
    20: "Mitsubishi",
    29: "Qualcomm",
    57: "Gensys",
    76: "Apple Inc.",
    80: "Innovative Systems",
    81: "Fitbit, Inc.",
    86: "Synopsys",
    87: "Sony",
    89: "Nordic Semiconductor",
    93: "Realtek Semiconductor",
    117: "Samsung Electronics",
    141: "Philips Lighting",
    152: "Garmin",
    196: "Bose Corporation",
    224: "Google",
    269: "Beats Electronics",
    338: "Nintendo",
    343: "Logitech",
    347: "LG Electronics",
    388: "Xiaomi Inc.",
    637: "Huawei Technologies Co., Ltd.",
    708: "Tuya Smart",
    741: "Espressif Systems",
    841: "Tile, Inc.",
    895: "OnePlus Electronics",
    911: "Xiaomi Communications",
    1077: "Raspberry Pi Trading Ltd",
    1122: "Anker Innovations",
    1340: "Nothing Technology Limited",
    1850: "Amazon Lab126",
    2055: "Wyze Labs",
}

# Common Service UUIDs (Expanded standard 16-bit and 128-bit)
SERVICE_UUIDS = {
    "00001800-0000-1000-8000-00805f9b34fb": "Generic Access",
    "00001801-0000-1000-8000-00805f9b34fb": "Generic Attribute",
    "0000180a-0000-1000-8000-00805f9b34fb": "Device Information",
    "0000180f-0000-1000-8000-00805f9b34fb": "Battery Service",
    "0000180d-0000-1000-8000-00805f9b34fb": "Heart Rate",
    "00001805-0000-1000-8000-00805f9b34fb": "Current Time",
    "00001821-0000-1000-8000-00805f9b34fb": "Indoor Positioning",
    "00001819-0000-1000-8000-00805f9b34fb": "Location and Navigation",
    "00001827-0000-1000-8000-00805f9b34fb": "Mesh Provisioning",
    "00001828-0000-1000-8000-00805f9b34fb": "Mesh Proxy",
    "00001812-0000-1000-8000-00805f9b34fb": "Human Interface Device (HID)",
    "00001810-0000-1000-8000-00805f9b34fb": "Blood Pressure",
    "0000181a-0000-1000-8000-00805f9b34fb": "Environmental Sensing",
    "0000fe9f-0000-1000-8000-00805f9b34fb": "Google (Chromecast/Smart Home)",
    "0000feed-0000-1000-8000-00805f9b34fb": "Tile, Inc.",
    "0000fd6f-0000-1000-8000-00805f9b34fb": "COVID-19 Exposure Notification",
    "0000feaa-0000-1000-8000-00805f9b34fb": "Google Eddystone",
    "0000fe2c-0000-1000-8000-00805f9b34fb": "Google Fast Pair",
}

# Common GATT Characteristic UUIDs
CHARACTERISTIC_UUIDS = {
    "00002a00-0000-1000-8000-00805f9b34fb": "Device Name",
    "00002a01-0000-1000-8000-00805f9b34fb": "Appearance",
    "00002a19-0000-1000-8000-00805f9b34fb": "Battery Level",
    "00002a24-0000-1000-8000-00805f9b34fb": "Model Number String",
    "00002a25-0000-1000-8000-00805f9b34fb": "Serial Number String",
    "00002a26-0000-1000-8000-00805f9b34fb": "Firmware Revision String",
    "00002a27-0000-1000-8000-00805f9b34fb": "Hardware Revision String",
    "00002a28-0000-1000-8000-00805f9b34fb": "Software Revision String",
    "00002a29-0000-1000-8000-00805f9b34fb": "Manufacturer Name String",
    "00002a37-0000-1000-8000-00805f9b34fb": "Heart Rate Measurement",
    "00002a6e-0000-1000-8000-00805f9b34fb": "Temperature",
}

APPLE_CONTINUITY_TYPES = {
    0x02: "Apple iBeacon",
    0x05: "Apple AirDrop",
    0x07: "Apple AirPods",
    0x08: "Apple AirPlay Source",
    0x09: "Apple AirPlay Target",
    0x0A: "Apple Watch / Companion",
    0x0B: "Apple HomeKit",
    0x0C: "Apple Handoff",
    0x0D: "Apple Wi-Fi Password Sharing",
    0x0E: "Apple Instant Hotspot",
    0x10: "Apple Nearby",
    0x12: "Apple Find My (AirTag / Offline)",
}

def identify_apple_device(data_bytes: bytes) -> str:
    """
    Analyzes the payload for Apple Manufacturer ID 0x004C (76).
    Returns a string describing the probable device/packet type.
    Based on reverse-engineered specs of the Apple Continuity protocol.
    """
    if not data_bytes or len(data_bytes) < 1:
        return "Apple Device"
        
    type_byte = data_bytes[0]
    if type_byte in APPLE_CONTINUITY_TYPES:
        return APPLE_CONTINUITY_TYPES[type_byte]
    
    return f"Apple Device (Type: {hex(type_byte)})"

def classify_address(address: str) -> dict:
    """
    Analyzes a BLE hardware address (BD_ADDR) for privacy and randomization.
    Checks bit 1 of the most significant byte (locally vs universally administered),
    and classifies Random Private Addresses (RPA, NRPA, Static).
    """
    if not address or ":" not in address:
        return {
            "is_random": None,
            "type_name": "Unknown",
            "tag": "UNK"
        }

    try:
        first_byte = int(address.split(":")[0], 16)
        is_random = bool(first_byte & 0x02)
        
        if not is_random:
            return {
                "is_random": False,
                "type_name": "Public (Trackable)",
                "tag": "PUB"
            }

        msb_bits = (first_byte >> 6) & 0x03
        if msb_bits == 0b11:
            type_name = "Static Random"
        elif msb_bits == 0b01:
            type_name = "Resolvable Private (RPA)"
        elif msb_bits == 0b00:
            type_name = "Non-Resolvable Private (NRPA)"
        else:
            type_name = "Random Private"

        return {
            "is_random": True,
            "type_name": type_name,
            "tag": "RAND"
        }
    except Exception:
        return {
            "is_random": None,
            "type_name": "Unknown",
            "tag": "UNK"
        }
