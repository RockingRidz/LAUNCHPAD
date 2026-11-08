"""Read-only installation checks. Never drives GPIO or uploads local settings."""
import argparse
import importlib.util
import json
from pathlib import Path
import platform
import sys
from server import load_config

ROOT = Path(__file__).resolve().parent

def checks(config, hardware=False):
    result = []
    def add(status, name, detail): result.append(dict(status=status, name=name, detail=detail))
    add('PASS' if sys.version_info >= (3, 9) else 'FAIL', 'Python', platform.python_version())
    for package in ['PIL', 'skyfield'] + (['spidev', 'gpiozero'] if hardware else []):
        add('PASS' if importlib.util.find_spec(package) else 'FAIL', package, 'Installed' if importlib.util.find_spec(package) else 'Install requirements.txt')
    try:
        cfg = load_config(config)
        add('PASS', 'Configuration', 'Valid; private coordinates omitted')
        add('WARN' if cfg.get('latitude') is None else 'PASS', 'Observing location', 'Missing: local passes and weather unavailable' if cfg.get('latitude') is None else 'Configured')
        add('PASS', 'Buzzer', 'Enabled' if cfg.get('buzzer_enabled') else 'Disabled')
    except (OSError, ValueError, TypeError, KeyError) as exc:
        add('FAIL', 'Configuration', type(exc).__name__ + ': use a valid config.example.json copy')
    if hardware:
        for device in ['/dev/spidev0.0', '/dev/spidev0.1']:
            add('PASS' if Path(device).exists() else 'FAIL', device, 'Present' if Path(device).exists() else 'Enable SPI and reboot on the Pi')
        path = ROOT / 'touch-calibration.json'
        try:
            raw = json.loads(path.read_text(encoding='utf-8'))['raw']
            valid = len(raw) == 2 and all(len(p) == 2 for p in raw) and all(abs(raw[1][i]-raw[0][i]) >= 300 for i in (0, 1))
            if not valid: raise ValueError()
            add('PASS', 'Touch calibration', 'Two distinct points saved; verify on the physical screen')
        except (OSError, ValueError, TypeError, KeyError):
            add('FAIL', 'Touch calibration', 'Run lcd_client.py --calibrate on the Pi')
        add('WARN', 'LCD revision', 'Confirm ST7789 before wiring; controller cannot be verified here')
    return result

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--hardware', action='store_true')
    parser.add_argument('--json', action='store_true')
    parser.add_argument('--config', type=Path, default=ROOT/'config.json')
    args = parser.parse_args()
    config = args.config if args.config.exists() else ROOT/'config.example.json'
    results = checks(config, args.hardware)
    if args.json: print(json.dumps(results, indent=2))
    else:
        for item in results: print('{status:4}  {name}: {detail}'.format(**item))
    return int(any(item['status'] == 'FAIL' for item in results))

if __name__ == '__main__': raise SystemExit(main())
