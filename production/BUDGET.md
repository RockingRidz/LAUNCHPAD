# Final budget — 8 November 2026

The final minimum-cost BOM is Rs5640, not Rs3500. This is a mixed sourced/estimated budget, not an available checkout basket.

Changes from the earlier Rs5491 own-printer estimate:

- Existing battery and LM2596 replace the Rs450 supply allowance: minus Rs450.
- Robu six-part print quote Rs951 replaces Rs300 own-print allowance: plus Rs651.
- Omit optional buzzer, transistor, diode, two resistors and their breadboard: minus Rs102.
- Allow a buck-to-micro-USB lead/connector: plus Rs50.

Reconciliation: 5491 - 450 + 651 - 102 + 50 = 5640. The Rs250 delivery allowance remains included; actual shipping may differ. The optional buzzer circuit costs an estimated Rs102 to add back. This is a reduction of Rs102 versus the equivalent powered, commercially printed full-feature build with the same Rs50 cable allowance.

The owner reports existing power hardware; stable 5V operation has not been tested. It stays external to the enclosure. Buzzer is disabled in the example configuration. No claimed saving assumes a donated microSD or free printing, since neither was confirmed.

Sources checked 8 November: the selected Hubtronics display still lists Rs1475 incl GST, stock 2, but advertises HX8347D; ST7789 revision must be confirmed. Thingbits lists a Rs1770 Pi Zero 2 W but marks it sold out, so that lower price is not counted. The Pi Rs2079 line remains an earlier Nov7 observation, not freshly verified stock/checkout pricing. Other small component prices remain estimates.

- https://hubtronics.in/display-devices/lcds/other-lcds/2.8inch-resistive-touch-lcd
- https://thingbits.in/products/raspberry-pi-zero-2-w
- https://robu.in/product-category/raspberry-pi-zero/
- Robu print quote: PRINT-QUOTE.md

To reach Rs3500, another Rs2140 must be removed. Even free printing alone leaves Rs4689. That requires a separately verified cheaper display/Pi purchase or confirmed reused parts; changing the screen needs CAD, wiring and driver changes. No last-minute untested substitution is included in this submission.
