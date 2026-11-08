import unittest
from dataclasses import asdict
from flight import Flight

class FlightTests(unittest.TestCase):
    def test_pause_freezes_and_resume_continues(self):
        f = Flight(throttle=1)
        f.toggle(); f.step(.1); f.toggle()
        before = asdict(f)
        f.step(10)
        self.assertEqual(asdict(f), before)
        f.toggle(); f.step(.1)
        self.assertGreater(f.height, before['height'])

    def test_success_is_terminal(self):
        f = Flight(throttle=1)
        f.toggle()
        for _ in range(3000): f.step(.1)
        self.assertEqual(f.message, 'TARGET REACHED')
        self.assertGreaterEqual(f.height, f.target)
        before = asdict(f)
        f.toggle(); f.step(.1)
        self.assertEqual(asdict(f), before)
        self.assertGreaterEqual(f.fuel, 0)

    def test_landing_requires_reset(self):
        f = Flight(throttle=0)
        f.toggle(); f.step(.1)
        self.assertTrue(f.finished)
        self.assertEqual(f.height, 0)

    def test_stage_once_and_only_in_flight(self):
        f = Flight()
        f.separate(); self.assertEqual(f.dry, 14)
        f.toggle(); f.separate(); f.separate()
        self.assertEqual((f.stage, f.dry), (2, 10))

if __name__ == '__main__': unittest.main()
