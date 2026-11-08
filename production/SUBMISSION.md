# LAUNCHPAD

LAUNCHPAD is a rocket-shaped Raspberry Pi Zero 2 W mission-control computer. Its custom enclosure holds a small SPI touchscreen with five modes: ISS tracking and predicted passes, rocket launch countdowns, mission briefs, local observing weather, and an offline educational flight simulator. On-screen controls replace a separate controller. A removable nose and rear service cover provide access to the wired assembly.

## Included design files

FreeCAD source with STEP/STL exports, KiCad schematic with PDF and wiring netlist, Python firmware, native portrait touchscreen client, browser interface, build instructions, sources, BOM and print quote layout. No fabricated PCB is required. Optional buzzer hardware is shown but omitted from the minimum-cost BOM.

## Validation

Unbuilt prototype design. Sixteen Python tests, browser simulation checks and wiring-netlist checks pass. KiCad ERC has zero errors and warnings. The six printed CAD parts are digitally valid solids with recorded collision checks against each other and the manufacturer's display model. No physical printing, assembly, power/load, touchscreen or Pi deployment test is claimed. Confirm ST7789 display stock before buying; the selected retailer advertises an older controller under the same SKU.

## Budget

Estimated remaining spend: Rs5640 including a Rs951 six-part printing quote, Rs250 delivery allowance and Rs50 power-lead allowance. Existing battery and LM2596 are counted at zero. Smaller parts and Pi availability/pricing still require purchase-time confirmation. This design is not a confirmed Rs3500 build.

Repository: https://github.com/RockingRidz/LAUNCHPAD
