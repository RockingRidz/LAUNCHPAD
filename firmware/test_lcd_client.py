import unittest
from unittest.mock import Mock
from lcd_client import Display,touch_point

class TouchTests(unittest.TestCase):
    def test_inactive_pen_does_not_read_spi(self):
        d=Display.__new__(Display);d.irq=Mock(is_active=False);d.touch=Mock()
        self.assertIsNone(d.raw_touch());d.touch.xfer2.assert_not_called()
    def test_active_low_pen_reads_both_axes(self):
        d=Display.__new__(Display);d.irq=Mock(is_active=True);d.touch=Mock()
        d.touch.xfer2.return_value=[0,32,0]
        self.assertEqual(d.raw_touch(),(1024,1024));self.assertEqual(d.touch.xfer2.call_count,10)
    def test_calibration_maps_corners(self):
        cal={'raw':[[300,400],[3800,3700]]}
        self.assertEqual(touch_point((300,400),cal),(20,30))
        self.assertEqual(touch_point((3800,3700),cal),(220,290))

if __name__=='__main__':unittest.main()
