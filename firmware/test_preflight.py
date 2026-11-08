import json
from pathlib import Path
import tempfile
import unittest
from preflight import checks

class PreflightTests(unittest.TestCase):
    def test_private_coordinates_not_reported(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'config.json'
            path.write_text(json.dumps({'latitude':12.345678,'longitude':76.54321}),encoding='utf-8')
            result=checks(path)
            self.assertNotIn('12.345678',json.dumps(result))
            self.assertNotIn('76.54321',json.dumps(result))
            self.assertEqual(next(r['status'] for r in result if r['name']=='Observing location'),'PASS')

    def test_invalid_config_is_actionable_failure(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'config.json'
            path.write_text('{broken',encoding='utf-8')
            self.assertEqual(next(r['status'] for r in checks(path) if r['name']=='Configuration'),'FAIL')

if __name__=='__main__':unittest.main()
