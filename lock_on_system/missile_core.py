"""Missile core utilities for steering and subsystem attachment."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Protocol

from .lock_on import Vector3, _normalize


class RadarModule(Protocol):
    """Interface a radar module must implement to receive guidance updates."""

    def on_course_update(self, position: Vector3, heading: Vector3) -> None:
        """Called when the missile's course changes."""


class EngineModule(Protocol):
    """Interface an engine module must expose for telemetry."""

    def fuel_remaining(self) -> float:
        """Return remaining fuel mass/volume in arbitrary units."""

    def fuel_capacity(self) -> float:
        """Return total fuel capacity in the same units as :meth:`fuel_remaining`."""

    def current_fuel_consumption(self) -> float:
        """Return current fuel consumption rate per second."""


@dataclass
class EngineReport:
    """Summarized engine telemetry for consumers."""

    fuel_remaining: float
    fuel_capacity: float
    consumption_rate: float
    reserve_seconds: Optional[float] = None


@dataclass
class MissileCore:
    """Main missile core with steering and subsystem ports."""

    position: Vector3 = (0.0, 0.0, 0.0)
    heading: Vector3 = (1.0, 0.0, 0.0)
    radar: Optional[RadarModule] = None
    engine: Optional[EngineModule] = None
    _normalized_heading: Vector3 = field(init=False, default=(1.0, 0.0, 0.0))

    def __post_init__(self) -> None:
        self._normalized_heading = _normalize(self.heading)

    def connect_radar(self, radar: RadarModule) -> None:
        """Attach a radar module and push the current course immediately."""

        self.radar = radar
        self._push_course_update()

    def connect_engine(self, engine: EngineModule) -> None:
        """Attach an engine module for telemetry queries."""

        self.engine = engine

    def steer(self, heading: Vector3) -> None:
        """Update the missile heading and notify connected radar."""

        self.heading = heading
        self._normalized_heading = _normalize(heading)
        self._push_course_update()

    def relocate(self, position: Vector3) -> None:
        """Update the missile position and notify connected radar."""

        self.position = position
        self._push_course_update()

    def _push_course_update(self) -> None:
        if self.radar is None:
            return
        self.radar.on_course_update(self.position, self._normalized_heading)

    def engine_report(self) -> EngineReport:
        """Return fuel telemetry based on the attached engine module."""

        if self.engine is None:
            raise RuntimeError("Engine module not connected")

        remaining = self.engine.fuel_remaining()
        capacity = self.engine.fuel_capacity()
        consumption = self.engine.current_fuel_consumption()
        reserve = None if consumption <= 0 else remaining / consumption

        return EngineReport(
            fuel_remaining=remaining,
            fuel_capacity=capacity,
            consumption_rate=consumption,
            reserve_seconds=reserve,
        )
