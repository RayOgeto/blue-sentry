import unittest
import sys
import os

# Add parent directory to path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import vendors

class TestVendorLogic(unittest.TestCase):
    
    def test_company_lookup(self):
        """Test that we can correctly identify major companies."""
        self.assertEqual(vendors.COMPANY_IDS.get(76), "Apple Inc.")
        self.assertEqual(vendors.COMPANY_IDS.get(6), "Microsoft")
        self.assertEqual(vendors.COMPANY_IDS.get(117), "Samsung Electronics")
        self.assertEqual(vendors.COMPANY_IDS.get(741), "Espressif Systems")
        self.assertEqual(vendors.COMPANY_IDS.get(1077), "Raspberry Pi Trading Ltd")
        
    def test_service_lookup(self):
        """Test service UUID resolution."""
        uuid = "0000180d-0000-1000-8000-00805f9b34fb"
        self.assertEqual(vendors.SERVICE_UUIDS.get(uuid), "Heart Rate")

    def test_apple_identification(self):
        """Test the logic for identifying Apple device types."""
        # Type 0x05 = AirDrop
        data = bytes([0x05, 0x12, 0x34])
        self.assertEqual(vendors.identify_apple_device(data), "Apple AirDrop")
        
        # Type 0x10 = Nearby
        data = bytes([0x10, 0x00])
        self.assertEqual(vendors.identify_apple_device(data), "Apple Nearby")

        # Type 0x12 = Find My
        data = bytes([0x12, 0x19, 0x00])
        self.assertEqual(vendors.identify_apple_device(data), "Apple Find My (AirTag / Offline)")
        
        # Unknown Type
        data = bytes([0xFF, 0x00])
        self.assertIn("Type: 0xff", vendors.identify_apple_device(data))

    def test_address_classification(self):
        """Test BD_ADDR IEEE randomization and privacy classification."""
        # Public address (bit 1 is 0: e.g. 0x00, 0x48, etc.)
        pub_addr = "48:F4:7B:D4:98:8D"
        res_pub = vendors.classify_address(pub_addr)
        self.assertFalse(res_pub["is_random"])
        self.assertEqual(res_pub["tag"], "PUB")

        # Resolvable Private Address (RPA: bit 1 is 1, top two bits 01 -> e.g. 0x42, 0x5A)
        # 0x42 = 0100 0010 (bit 1 is 1, bits 7..6 are 01)
        rpa_addr = "42:AB:CD:11:22:33"
        res_rpa = vendors.classify_address(rpa_addr)
        self.assertTrue(res_rpa["is_random"])
        self.assertIn("Resolvable Private", res_rpa["type_name"])
        self.assertEqual(res_rpa["tag"], "RAND")

        # Static Random Address (top two bits 11 -> e.g. 0xCE, 0xFE, 0xC0)
        # 0xCE = 1100 1110
        static_addr = "CE:11:22:33:44:55"
        res_static = vendors.classify_address(static_addr)
        self.assertTrue(res_static["is_random"])
        self.assertEqual(res_static["type_name"], "Static Random")

        # Non-colon / macOS UUID fallback
        uuid_addr = "E621E1F8-C36C-495A-93FC-0C247A3E6E5F"
        res_uuid = vendors.classify_address(uuid_addr)
        self.assertIsNone(res_uuid["is_random"])
        self.assertEqual(res_uuid["tag"], "UNK")

if __name__ == '__main__':
    unittest.main()
