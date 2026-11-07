import unittest,tempfile,json,time
from pathlib import Path
from unittest.mock import Mock,patch
import server

class StationTests(unittest.TestCase):
    def test_cache_survives_network_failure_and_backs_off(self):
        with tempfile.TemporaryDirectory() as tmp:
            loader=Mock(side_effect=[{'ok':True},RuntimeError('offline')])
            f=server.Feed('test',10,loader,Path(tmp));f.update(100)
            self.assertEqual(f.data,{'ok':True});f.update(120);f.update(121)
            self.assertEqual(loader.call_count,2);self.assertEqual(f.data,{'ok':True})
            self.assertIn('offline',f.error)
            restored=server.Feed('test',10,loader,Path(tmp));self.assertEqual(restored.data,{'ok':True})
    def test_invalid_coordinates_rejected(self):
        for config in [{'latitude':91,'longitude':0},{'latitude':1,'longitude':None},{'latitude':float('nan'),'longitude':0}]:
            with tempfile.TemporaryDirectory() as tmp:
                p=Path(tmp)/'config.json';p.write_text(json.dumps(config))
                with self.assertRaises(ValueError):server.load_config(p)
    def test_pass_alert_only_once_and_not_with_stale_orbit(self):
        s=server.Station({'alert_seconds':120},demo=True)
        event={'rise':1100,'set':1300};s.check_alerts({'passes':[event],'stale':True},1000)
        self.assertFalse(s.alerts)
        s.check_alerts({'passes':[event]},1000);s.check_alerts({'passes':[event]},1001)
        self.assertEqual(len(s.alerts),1)
    def test_demo_is_labelled_and_contains_all_feed_groups(self):
        state=server.Station({},demo=True).snapshot();self.assertTrue(state['demo'])
        for key in ('iss','launches','weather','orbit','alerts'):self.assertIn(key,state)
        self.assertIn('fictional',state['launches']['data'][0]['rocket'])
    def test_without_location_weather_does_not_send_coordinates(self):
        s=server.Station({},demo=True)
        with patch('server.fetch_json') as fetch:
            self.assertEqual(s.weather(),{'location_required':True});fetch.assert_not_called()

if __name__=='__main__':unittest.main()
