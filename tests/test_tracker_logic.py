import unittest
import sys
import os
import time
from unittest.mock import MagicMock

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import tracker

class TestTrackerLogic(unittest.TestCase):

    def test_bloodhound_tracker_initialization(self):
        """Verify tracker starts with clean deque structures and defaults."""
        bh = tracker.BloodhoundTracker("AA:BB:CC:11:22:33")
        self.assertEqual(bh.target_mac, "AA:BB:CC:11:22:33")
        self.assertEqual(len(bh.rssi_history), 0)
        self.assertEqual(bh.current_rssi, -100)
        self.assertIsNone(bh.smoothed_rssi)

    def test_detection_callback_matching(self):
        """Verify detection_callback updates values only for matching MAC."""
        bh = tracker.BloodhoundTracker("AA:BB:CC:11:22:33")

        # Non-matching device
        mock_other = MagicMock()
        mock_other.address = "00:11:22:33:44:55"
        mock_ad_other = MagicMock()
        mock_ad_other.rssi = -45
        mock_ad_other.local_name = "OtherDevice"
        bh.detection_callback(mock_other, mock_ad_other)

        self.assertEqual(bh.current_rssi, -100)
        self.assertEqual(bh.packet_count, 0)

        # Matching device
        mock_target = MagicMock()
        mock_target.address = "AA:BB:CC:11:22:33"
        mock_ad_target = MagicMock()
        mock_ad_target.rssi = -60
        mock_ad_target.local_name = "TargetBeacon"
        bh.detection_callback(mock_target, mock_ad_target)

        self.assertEqual(bh.current_rssi, -60)
        self.assertEqual(bh.device_name, "TargetBeacon")
        self.assertEqual(bh.packet_count, 1)

    def test_ema_smoothing_and_deque_bounds(self):
        """Verify EMA calculation and history ring buffer length constraint."""
        bh = tracker.BloodhoundTracker("AA:BB:CC:11:22:33")
        bh.target_mac = "AA:BB:CC:11:22:33"

        # Simulate 70 ticks
        mock_target = MagicMock()
        mock_target.address = "AA:BB:CC:11:22:33"
        mock_ad = MagicMock()
        mock_ad.local_name = "TargetBeacon"

        for i in range(70):
            mock_ad.rssi = -50 if i % 2 == 0 else -70
            bh.detection_callback(mock_target, mock_ad)
            bh.tick()

        # Maximum history length must not exceed HISTORY_SIZE (50)
        self.assertEqual(len(bh.rssi_history), tracker.HISTORY_SIZE)
        self.assertEqual(len(bh.smoothed_history), tracker.HISTORY_SIZE)
        
        # Smoothed RSSI should be between -50 and -70
        self.assertIsNotNone(bh.smoothed_rssi)
        self.assertGreater(bh.smoothed_rssi, -70)
        self.assertLess(bh.smoothed_rssi, -50)

if __name__ == '__main__':
    unittest.main()
