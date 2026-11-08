"""Hardware-independent vertical flight model for the portrait display."""
from dataclasses import dataclass
import math

@dataclass
class Flight:
    target: int = 1000
    height: float = 0.
    velocity: float = 0.
    peak: float = 0.
    elapsed: float = 0.
    fuel: float = 36.
    throttle: float = .7
    angle: int = 0
    stage: int = 1
    dry: float = 14.
    running: bool = False
    paused: bool = False
    finished: bool = False
    message: str = 'Set throttle, then ignite'

    def toggle(self):
        if self.finished:
            return
        if not self.running:
            self.running = True
            self.message = 'Flight underway'
        else:
            self.paused = not self.paused
            self.message = 'PAUSED' if self.paused else 'Flight resumed'

    def separate(self):
        if self.running and not self.paused and self.stage == 1:
            self.stage = 2
            self.dry -= 4

    def step(self, dt):
        if not self.running or self.paused or self.finished:
            return
        dt = max(0., min(dt, .1))
        mass = self.dry + self.fuel
        used = min(self.fuel, 1.4 * self.throttle * dt)
        thrust = 780 * self.throttle if used > 0 else 0
        self.fuel = max(0., self.fuel - used)
        self.velocity += (math.cos(math.radians(self.angle)) * thrust / mass - 9.81
                          - .018 * self.velocity * abs(self.velocity) / mass) * dt
        self.height += self.velocity * dt
        self.elapsed += dt
        self.peak = max(self.peak, self.height)
        if self.height >= self.target:
            self.message = 'TARGET REACHED'
            self.finished = True
        elif abs(self.angle) > 70:
            self.message = 'Excessive tilt - reset'
            self.finished = True
        elif self.height <= 0:
            self.height = self.velocity = 0.
            self.message = 'Landed - reset to retry'
            self.finished = True
        if self.finished:
            self.running = False
