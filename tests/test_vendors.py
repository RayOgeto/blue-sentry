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
        
        # Unknown Type
        data = bytes([0xFF, 0x00])
        self.assertIn("Type: 0xff", vendors.identify_apple_device(data))

if __name__ == '__main__':
    unittest.main()
