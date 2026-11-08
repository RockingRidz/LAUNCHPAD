# Validation status — 7 November 2026

This is a design/source package for an unbuilt prototype. It is not a physically verified production release.

Completed:

- FreeCAD 1.0.2 generated six printed parts: barrel, nose, cover, carrier and two LCD retainers. Each exported part is a valid single solid. Geometry report included in `/cad`.
- Native FreeCAD, STEP and STL files generated, with editable Python/JSON regeneration sources. Printed-part collision check reports no overlaps. Local comparison to Waveshare’s official 69-solid LCD STEP reports zero intersections for every printed part.
- KiCad CLI successfully opened the schematic and exported PDF, SVG and XML netlist.
- KiCad electrical rules check: zero reported violations (ERC.rpt).
- Netlist checked for Pi-to-LCD logical signal mappings, buzzer GPIO/base resistor, NPN emitter/base/collector, diode polarity and common ground. See `check_netlist.py`.
- Ten Python unit tests pass: caching/backoff, coordinate validation, stale-orbit alert suppression/deduplication, labelled demo feeds, no weather request without configured location, active-low touch IRQ handling and calibration corner mapping.
- Python compilation and JavaScript syntax checks pass.
- Browser demo rendered ISS Watch, Launch Clock, Mission Brief, Skywatch and Flight Sim. Clicking a launch opens its brief. Ignition changed the simulator to flight-in-progress and consumed fuel.

Not verified:

- Real screen/controller revision, SPI initialization, colour order, backlight and touch calibration.
- Real GPIO buzzer and circuit current, soldering, connector orientation, power draw and thermal behaviour.
- Real module fit, active-area offset, printed tolerances, supports, PCB edge clip retention and centre of gravity.
- API connectivity, live data accuracy, launch-provider throttling and actual ISS pass observations. Desktop demo testing is not live-service validation.
- End-to-end Pi deployment and automatic startup.

The selected supplier page advertises HX8347D while current manufacturer instructions describe ST7789 stock. Confirm ST7789 before purchase; otherwise choose a compatible seller or implement and test an HX8347D driver. Do not silently substitute the controller.

No custom PCB layout or Gerbers exist because this design uses a wired assembly. No fake manufacturing ZIP is included.

Update 0.5 adds tests for visible-only alerts, stable demo schedules and JavaScript checks for compass wrapping, successful flight, nonnegative fuel, pause, landing, tilt failure and custom targets. Fit coupons are valid single solids; their material estimates are in `cad/fit-checks/fit-checks.json`. Core enclosure geometry and hardware mapping are unchanged.

## Revision 0.6 software validation

Sixteen Python tests pass, including native flight pause/resume, terminal success/landing, one-time staging and private-coordinate omission in preflight reports. Browser physics checks and netlist mapping checks also pass. The read-only preflight checker correctly reports missing Skyfield and observing coordinates on the development installation; these are installation requirements, not a verified Pi setup. No GPIO or physical display was exercised.
