# Build LAUNCHPAD

This is a wired Raspberry Pi prototype, not a PCB manufacturing package. Files are an unbuilt design release. Desktop software and digital checks are testable now; physical fit, LCD initialization, touch and GPIO alerts require bench validation.

## Selected parts

Pi Zero 2 W and Waveshare **2.8inch Resistive Touch LCD, SKU16446, ST7789 revision**, not the Arduino shield, Pico board or RPi LCD(A). The vendor has shipped both HX8347D and ST7789 controllers under this product name. Confirm ST7789 with the seller before purchase. The direct display client does not support HX8347D.

The selected display replaces the unspecified 2.3-inch panel with the user's authorization to choose a screen. Manufacturer dimensions: PCB 79.9 x 50.8 mm; active display 57.6 x 43.2 mm. The design uses portrait orientation. Verify active-area offset, connector projection and glass stack height on the purchased module; these are not established by the outline dimensions alone.

## Print and mechanical assembly

1. Open `cad/LAUNCHPAD.FCStd` in FreeCAD. `cad/parameters.json` and `cad/build_rocket_v2.py` are the regeneration sources. Editing the spreadsheet alone does not regenerate the Boolean model: change the JSON and rerun the script using FreeCAD's Python.
2. Print a cheap aperture coupon before the full body. Current opening is 44.2 x 58.6 mm with nominal 1 mm active-area clearance. Check against your actual panel and adjust the opening and pocket in the source if needed. The rear-open pocket is 51.6 x 80.8 mm. Two removable retainer bridges attach to four M3 pilot bosses and contact only the PCB edge through approximately 1 mm foam pads. Do not force or clamp the glass.
3. Slice `RocketBody.stl` upright, `NoseCone.stl` upright with its plug on the bed, `RearCover.stl` on its broad face, `PiCarrier.stl` flat with posts upward, and both `LCDRetainer*.stl` bridges on their broad faces. Rotate the cover and retainers in the slicer as needed; exported coordinates preserve their assembly axes. Starting settings: PLA, 0.2 mm layers, 3 walls, 15% infill. Use a brim and inspect supports around the display pocket/clip overhangs and USB cable opening. Supports and bed adhesion depend on your printer.
4. The assembled rocket is 205 mm high and roughly 113 x 107 mm overall. The barrel is 150 mm tall and the removable nose has a 63 mm print envelope, so they can be printed separately on a smaller printer. The nose plug has 0.3 mm radial clearance; test its fit and use small removable tape shims if loose. Do not scale the entire model to fit; that changes the screen and screw dimensions.
5. Use thin foam tape around the PCB border to eliminate movement and to support light stylus pressure. Keep adhesive off the display, ribbon and components. Install through the open top with the nose removed, then secure the two retainer bridges from the rear using four M3 x10 self-tapping screws. The front shoulder and gasket support the panel; retainer pads support the PCB edges. Never use screw force to bend the board or glass.
6. Mount the Pi on the carrier's four 58 x 23 mm hole centres. Use M2.5 nylon screws and spacers. Carrier stands vertically behind the screen in the assembly STEP. Attach through rear-cover holes using approximately 4 mm nylon spacers; verify screw engagement and avoid contact with the Pi's underside. Select screw length after the actual stack is assembled (allowance: M2.5 x20 plus shorter screws).
7. Route a right-angle micro-USB power lead through the side opening with strain relief. The opening is a cable passage, not a precisely aligned panel socket. Position the Pi to suit the lead.
8. If fitting optional sound alerts, mount the buzzer driver on a mini breadboard or hand-soldered perfboard, insulate its underside, and secure it with foam tape. Secure wiring away from the Pi antenna and vents. Rear cover uses four M3 x10 self-tapping screws in printed pilot bosses; test screw fit on scrap first.

CAD solid volume implies approximately 210-230 g of PLA before slicer supports/changes. This is a geometric estimate, not a weighed or sliced print. Budget approximately 300 g including supports and coupons. Robu's observed quote for the six-part set is Rs951 including GST, excluding coupons and delivery; see PRINT-QUOTE.md. This replaces the previous own-printer material allowance in the final BOM.

## Wire

Disconnect power. Follow `pcb/wiring.csv`, the named LCD pins and the KiCad schematic. Connector numbers on LCD1 are **logical harness labels**, not a claim about the module's physical header numbering. Verify printed signal names on the board.

The display is powered from the Pi's **5 V rail** but its control signals are **3.3 V logic**. Never connect 5 V to GPIO signals. SPI clock/MOSI/MISO are shared; LCD and touch have separate chip selects. The 5 V buzzer must draw no more than 20 mA for the proposed 2N3904/1k base drive. Its negative lead is switched by Q1; D1 cathode goes to +5 V and anode to the switched negative. Confirm E/B/C pinout from your transistor datasheet, not from package shape.

Power the Pi only through the power micro-USB port, using a suitable 5 V supply. The owner already has a 12V lithium-ion pack and LM2596 module. Keep both external to the rocket: no fitted battery/buck mounting or charging circuit is designed. Connect the battery to buck input with correct polarity; set and measure 5.0V before connecting the Pi, then verify stable output under the Pi/display load. Feed the regulated output through a suitable micro-USB power lead. Never connect 12V directly to the Pi. Use the battery manufacturer's matching charger; its exact capacity, protection and discharge rating remain unverified. Do not power the assembly via multiple supplies simultaneously.

## Install and run

Start on a normal computer before connecting hardware:

```sh
python firmware/server.py --demo
```

Open http://127.0.0.1:8080. Demo mode uses explicitly fictional launch data and does not issue real alerts. All five modes and the browser flight game work without Python dependencies or internet. A browser must support JavaScript/canvas.

On Raspberry Pi OS (Python 3.10+), enable SPI using Raspberry Pi Configuration/raspi-config, then:

```sh
python3 -m venv .venv
.venv/bin/pip install -r firmware/requirements.txt
cp firmware/config.example.json firmware/config.json
.venv/bin/python firmware/server.py
```

Set latitude and longitude manually in the private `config.json`. Leaving them null avoids location requests and disables local pass/weather calculations. Configured coordinates are sent to Open-Meteo for weather; orbital pass calculations happen locally. Do not commit your location. Quiet hours use the Pi's configured local timezone; set it correctly. Buzzer is disabled by default: enable only after the driver circuit is tested.

For the selected ST7789 LCD, run the low-overhead native client in another session:

```sh
.venv/bin/python firmware/lcd_client.py --calibrate
.venv/bin/python firmware/lcd_client.py
```

Tap the two calibration crosses. If the X/Y axes are swapped, calibrate with normal raw samples and run with `--swap-touch`. If display colours or orientation differ, check the purchased controller revision and adjust ST7789 MADCTL/inversion settings in `lcd_client.py`; this path has not been tested on physical hardware. Touch calibration stays private/local. The LCD menu has five tabs, and simulation uses an on-screen throttle bar, left/right, ignition, staging and reset. Browser game has a fuller 2D model; the tiny native client uses a simplified vertical model with tilt affecting lift.

## Automatic startup

First confirm manual startup works. Copy `production/launchpad.service` and `launchpad-lcd.service` to `/etc/systemd/system/`, edit User, WorkingDirectory and ExecStart to your install location, then enable them. The example assumes user `pi` and `/home/pi/LAUNCHPAD`; newer Pi installations may use a different username. The account needs access to SPI and GPIO groups. Do not run the web server as root.

## Recreate and verify

Run `python -m unittest discover -s firmware -p "test_*.py"`. Run `node --check firmware/static/app.js` for JavaScript syntax. Rebuild CAD with FreeCAD 1.0's bundled Python: `python cad/build_rocket_v2.py`. Rebuild schematic with KiCad 10 symbols available using `python pcb/build_schematic_v2.py`; set `KICAD_SYMBOL_DIR` if installed elsewhere. Export with `kicad-cli sch export svg`, `sch export netlist` and `sch export pdf`. See `VALIDATION.md` for actual checks and remaining physical checks.

No Gerbers are supplied because no board is being fabricated. `pcb/GERBERS-NOT-APPLICABLE.md` records this explicitly. The production folder includes reproduction instructions, services, sources and validation; STEP/STL and source remain in `/cad`.


## CAD revision 0.4 checks

`cad/geometry-check.json` records valid single solids, zero printed-part intersections and zero intersections with Waveshare’s official LCD STEP at the planned placement. Download the reference STEP ZIP from the source link in SOURCES.md, extract it locally and pass `--lcd-reference /path/to/2_8inch_resistive_touch_lcd.stp` when regenerating. The third-party STEP is not redistributed. `cad/OPEN_LAUNCHPAD.FCMacro` is an optional FreeCAD macro that colours the assembly and generates views; open it in FreeCAD and run it only after reviewing the included source. The native file includes grouped printed parts and simplified hardware references.

## Fit coupons and upgraded controls

Run `cad/make_fit_coupons.py` using FreeCAD Python. Print both nose rings to test the nominal 0.3 mm radial clearance, and the screen aperture coupon to check the purchased panel before the full barrel. These test pieces use approximately 10.4 g of geometric PLA before slicing.

`visible_passes_only: true` in local config suppresses alerts unless peak visibility is positively predicted. Browser simulation has selectable targets; changing targets resets the flight. Pause freezes physics. Best fuel results are stored only in that browser. The Pi client retains its smaller vertical model.

## Preflight and portrait controls (0.6)

From the repository root, run `.venv/bin/python firmware/preflight.py --hardware`. A FAIL exits with code 1; WARN identifies optional setup or a manual check. The checker does not drive GPIO, verify the LCD controller electrically, test the power supply, or contact remote services. Coordinates are omitted from its report. `--json` provides a machine-readable report. Install the requirements inside the project virtual environment before expecting dependency checks to pass.

On the native SIM screen, tap the target label before ignition to cycle 1000/2500/5000 m. Tap the throttle bar, IGNITE, then PAUSE/RESUME as needed. Tap STAGE once to discard dry mass. A landed or completed flight requires RESET. Holding a finger on a button does not repeat it. Switching away from SIM freezes its physics. Run `lcd_client.py --port 8082` if your server uses a non-default port.

This vertical model is educational and differs from the browser's two-axis model. Hardware frame timing limits its speed; it is not a real-time flight instrument. All controller, touch, power and mechanical checks still require the purchased hardware.

## Minimum-cost assembly

The final BOM sets buzzer, transistor, diode, both resistors and buzzer breadboard quantities to zero. Omit the entire buzzer branch (BZ1/Q1/D1/R1/R2); wire the Pi/display harness unchanged and keep `buzzer_enabled: false`. Do not bridge or improvise connections on the omitted branch. The full optional circuit remains in the schematic for future use. The five modes and on-screen alerts do not need it. No new screen or Pi model is substituted.
