"""Core lock-on logic for selecting and tracking airborne targets."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Iterable, Optional, Tuple

Vector3 = Tuple[float, float, float]


def _dot(a: Vector3, b: Vector3) -> float:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _norm(v: Vector3) -> float:
    return math.sqrt(_dot(v, v))


def _normalize(v: Vector3) -> Vector3:
    magnitude = _norm(v)
    if magnitude == 0:
        return (0.0, 0.0, 0.0)
    return (v[0] / magnitude, v[1] / magnitude, v[2] / magnitude)


def _subtract(a: Vector3, b: Vector3) -> Vector3:
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _distance(a: Vector3, b: Vector3) -> float:
    return _norm(_subtract(a, b))


@dataclass
class Target:
    """Simple data structure describing a target in the world."""

    identifier: str
    position: Vector3
    velocity: Vector3 = (0.0, 0.0, 0.0)
    heat_signature: float = 1.0

    def predicted_position(self, time: float) -> Vector3:
        """Return the position after ``time`` seconds assuming constant velocity."""

        return (
            self.position[0] + self.velocity[0] * time,
            self.position[1] + self.velocity[1] * time,
            self.position[2] + self.velocity[2] * time,
        )


@dataclass
class LockState:
    """State of the current lock."""

    target: Target | None = None
    progress: float = 0.0
    locked: bool = False
    last_seen: float = 0.0


@dataclass
class LockOnSystem:
    """A compact lock-on system that prioritizes nearby, hot targets.

    The system tracks a potential target, accumulating ``lock_on_time`` seconds
    of uninterrupted visibility before declaring a lock. Once locked, the
    system keeps the target as long as it remains within ``max_range`` and the
    ``fov_deg`` cone or until ``lost_lock_timeout`` seconds of occlusion have
    passed.
    """

    max_range: float = 2000.0
    fov_deg: float = 45.0
    lock_on_time: float = 1.0
    lost_lock_timeout: float = 0.5
    _state: LockState = field(default_factory=LockState, init=False)
    _current_time: float = 0.0

    def _is_visible(self, origin: Vector3, aim: Vector3, target_pos: Vector3) -> bool:
        to_target = _subtract(target_pos, origin)
        distance = _norm(to_target)
        if distance > self.max_range or distance == 0:
            return False

        aim_norm = _normalize(aim)
        dir_norm = _normalize(to_target)
        cos_angle = _dot(aim_norm, dir_norm)
        return cos_angle >= math.cos(math.radians(self.fov_deg))

    def _score(self, origin: Vector3, target: Target) -> float:
        distance = _distance(origin, target.position)
        if distance == 0:
            return float("inf")

        heat_component = target.heat_signature / distance
        proximity_component = max(self.max_range - distance, 0.0) / max(self.max_range, 1e-6)
        return heat_component + proximity_component

    def _pick_best(self, origin: Vector3, aim: Vector3, targets: Iterable[Target]) -> Optional[Target]:
        best: Optional[Target] = None
        best_score = -math.inf
        for target in targets:
            if not self._is_visible(origin, aim, target.position):
                continue
            score = self._score(origin, target)
            if score > best_score:
                best_score = score
                best = target
        return best

    def update(self, origin: Vector3, aim: Vector3, targets: Iterable[Target], dt: float) -> LockState:
        """Advance the lock state by ``dt`` seconds and return the current state.

        ``origin`` and ``aim`` define the sensor location and forward direction.
        ``targets`` is an iterable of candidate :class:`Target` objects.
        """

        self._current_time += max(dt, 0.0)
        best = self._pick_best(origin, aim, targets)

        state = self._state
        if state.locked and state.target and best and best.identifier == state.target.identifier:
            state.last_seen = self._current_time
            state.target = best
            return state

        if state.locked and state.target:
            if best and best.identifier == state.target.identifier:
                state.last_seen = self._current_time
            elif self._current_time - state.last_seen > self.lost_lock_timeout:
                self._state = LockState()
            return self._state

        if best and (state.target is None or best.identifier != state.target.identifier):
            state.target = best
            state.progress = 0.0

        if best and state.target and best.identifier == state.target.identifier:
            state.progress += dt
            state.last_seen = self._current_time
            if state.progress >= self.lock_on_time:
                state.locked = True
                state.progress = self.lock_on_time
        else:
            state.progress = 0.0
            state.target = None

        return state

    def status(self) -> LockState:
        """Return a copy of the current lock state."""

        return LockState(
            target=self._state.target,
            progress=self._state.progress,
            locked=self._state.locked,
            last_seen=self._state.last_seen,
        )
