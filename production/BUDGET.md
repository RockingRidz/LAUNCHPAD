# Can the complete build cost Rs3500?

**The current design does not fit Rs3500 when every part must be bought.** Its sourced/estimated BOM totals Rs5491 including an own-printer material allowance and delivery allowance. Several smaller prices remain estimates, not quotes.

The Pi price recorded in the BOM is Rs2079, and the chosen touchscreen is currently listed at Rs1475 including GST. Together these are Rs3554, before storage, power, wiring, enclosure or delivery. The Pi amount is a previous listing observation, not a newly verified checkout price. The screen supplier still advertises HX8347D, so ST7789 revision availability must be confirmed.

Screen source checked 8 November 2026: https://hubtronics.in/display-devices/lcds/other-lcds/2.8inch-resistive-touch-lcd

Ways a reduced build might fit:

- Buy a genuinely cheaper used Pi from a trusted seller, with a confirmed price and working Wi-Fi.
- Use a cheaper touchscreen with a documented controller. This needs a separate driver/wiring and enclosure fit revision; do not substitute it into the current drawing blindly.
- Reuse or borrow a suitable micro-USB power supply and branded microSD card.
- Obtain free printing through a school or makerspace. Paying a service can cost much more than the filament allowance.

These are cost-reduction options, **not a verified Rs3500 shopping basket**. No parts were purchased or substituted. The existing CAD and schematic still target the selected Waveshare module and Pi Zero 2 W.

The software upgrades add no new hardware requirements. Fit coupons in `cad/fit-checks/` let you test the nose and display opening using a small amount of filament before committing to the full print.
