# BlueSentry: Project Context & Educational Guide

## Project Overview
**BlueSentry** is a passive Bluetooth Low Energy (BLE) scanner and analyzer built with Python. It demonstrates how devices broadcast their presence and what information is leaked "over the air" without pairing.

## Key Concepts for Assignment

### 1. Advertising Packets (GAP)
Bluetooth LE devices (like your watch) constantly shout "I am here!" to let phones connect to them. These shouts are called **Advertising Packets**.
*   **What we capture:** The device's MAC Address, RSSI, and payload data.
*   **Security Insight:** Many devices broadcast their exact model name or even user-specific data (like "Ray's Watch") in these packets, which is a privacy risk.

### 2. RSSI (Received Signal Strength Indicator)
*   **Definition:** A measurement of the power present in a received radio signal.
*   **Usage:** Used to estimate distance. In BlueSentry, we sort by RSSI to show the closest devices at the top.
*   **Values:**
    *   **-40 to -55:** Very close (less than 1 meter).
    *   **-90:** Very weak (limit of detection).

### 3. Manufacturer Data
This is a specific field in the packet where companies put custom data.
*   **0x004C (76):** Apple.
*   **0x0006 (6):** Microsoft.
*   **0x0075 (117):** Samsung.
*   **Analysis:** We use this to identify the *brand* of the device even if the name is "Unknown".

### 4. UUIDs (Universally Unique Identifiers)
These 128-bit numbers define what "Services" a device offers.
*   **0x180D:** Heart Rate Service.
*   **0x180F:** Battery Service.
*   **Security Insight:** Identifying these services tells an attacker what the device is capable of (e.g., a medical device vs. a speaker) before they even try to connect.

## How to Run

1.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

2.  **Run the Scanner:**
    *   *Note: On Linux, accessing the Bluetooth adapter usually requires root privileges.*
    ```bash
    sudo python3 scanner.py
    ```

## Experiment Ideas
1.  **Hide & Seek:** Move your smart watch away from the computer and watch the **RSSI** value drop in real-time.
2.  **Privacy Check:** Turn your phone's Bluetooth OFF and ON. Does the **Address (MAC)** change? (This is MAC Randomization).
3.  **Identification:** Can you find a device that says "Unknown" as a name but has a known Manufacturer ID?
