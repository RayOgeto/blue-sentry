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
    117: "Samsung Electronics",
    152: "Garmin",
    196: "Bose Corporation",
    224: "Google",
    269: "Beats Electronics",
    338: "Nintendo",
    343: "Logitech",
    841: "Tile, Inc.",
    1122: "Anker Innovations",
    2055: "Wyze Labs",
    # Add more as needed...
}

# Common Service UUIDs (Expanded)
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
}

def identify_apple_device(data_bytes):
    """
    Analyzes the payload for Apple Manufacturer ID 0x004C (76).
    Returns a string describing the probable device/packet type.
    Based on reverse-engineered specs of the 'Continuity' protocol.
    """
    if not data_bytes or len(data_bytes) < 2:
        return "Apple Device"
        
    # The first byte usually indicates the type of message
    type_byte = data_bytes[0]
    
    # Common Apple Continuity Types
    if type_byte == 0x02:
        return "Apple iBeacon"
    elif type_byte == 0x05:
        return "Apple AirDrop"
    elif type_byte == 0x07:
        return "Apple AirPods"
    elif type_byte == 0x09:
        return "Apple AirPlay Target"
    elif type_byte == 0x0C:
        return "Apple Handoff"
    elif type_byte == 0x10:
        return "Apple Nearby"
    elif type_byte == 0x12:
        return "Apple Find My (AirTag?)"
    
    return f"Apple Device (Type: {hex(type_byte)})"
