import unittest
import sys
import os
from unittest.mock import MagicMock
import csv
import tempfile

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import scanner

class TestScannerLogic(unittest.TestCase):

    def setUp(self):
        # Clear detected_devices before each test
        scanner.detected_devices.clear()

    def test_process_device_clean_data(self):
        """Verify process_device produces clean data without UI markup."""
        mock_device = MagicMock()
        mock_device.address = "48:F4:7B:D4:98:8D"
        mock_device.name = "TestBeacon"

        mock_ad = MagicMock()
        mock_ad.local_name = "TestBeacon"
        mock_ad.rssi = -65
        # Apple AirDrop payload (Company ID 76, Type 0x05)
        mock_ad.manufacturer_data = {76: bytes([0x05, 0x12, 0x34])}
        mock_ad.service_uuids = ["0000180d-0000-1000-8000-00805f9b34fb"]

        scanner.process_device(mock_device, mock_ad)

        self.assertIn("48:F4:7B:D4:98:8D", scanner.detected_devices)
        entry = scanner.detected_devices["48:F4:7B:D4:98:8D"]

        self.assertEqual(entry["Name"], "TestBeacon")
        self.assertEqual(entry["RSSI"], -65)
        self.assertEqual(entry["Manufacturer"], "Apple AirDrop")
        self.assertIn("Heart Rate", entry["Services"])
        self.assertFalse(entry["IsRandom"])
        self.assertEqual(entry["Tag"], "PUB")

        # Crucial check: ensure NO Rich markup leaked into the model
        self.assertNotIn("[red]", entry["AddressType"])
        self.assertNotIn("[green]", entry["Tag"])
        for s in entry["Services"]:
            self.assertNotIn("[red]", s)

    def test_save_log_csv_purity(self):
        """Verify saved CSV contains pure text without terminal ANSI/Rich tags."""
        mock_device = MagicMock()
        mock_device.address = "CE:11:22:33:44:55"
        mock_device.name = "Fitness Tracker"

        mock_ad = MagicMock()
        mock_ad.local_name = "Fitness Tracker"
        mock_ad.rssi = -55
        mock_ad.manufacturer_data = {81: b"fitbit"}
        mock_ad.service_uuids = ["0000180f-0000-1000-8000-00805f9b34fb"]

        scanner.process_device(mock_device, mock_ad)

        with tempfile.NamedTemporaryFile(mode="w+", delete=False, suffix=".csv") as tmp:
            tmp_path = tmp.name

        try:
            scanner.save_log_to_file(tmp_path)
            
            with open(tmp_path, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                rows = list(reader)

            self.assertGreaterEqual(len(rows), 2)
            header = rows[0]
            data_row = rows[1]

            self.assertEqual(header[0], "Address")
            self.assertEqual(data_row[0], "CE:11:22:33:44:55")
            self.assertEqual(data_row[1], "Fitness Tracker")
            self.assertEqual(data_row[2], "Fitbit, Inc.")
            self.assertEqual(data_row[3], "-55")
            self.assertIn("Battery Service", data_row[4])

            # Ensure no Rich tags in any cell
            for cell in data_row:
                self.assertNotIn("[", cell)
                self.assertNotIn("]", cell)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

if __name__ == '__main__':
    unittest.main()
