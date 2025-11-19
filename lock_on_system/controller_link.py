"""Utilities to connect the lock-on system to a missile main controller."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Optional, Protocol

from .lock_on import LockOnSystem, LockState, Target, Vector3


class MissileMainController(Protocol):
    """Minimal interface the missile's main controller should expose."""

    def set_tracking_target(self, target: Optional[Target]) -> None:
        """Inform the controller of the currently tracked (not necessarily locked) target."""

    def on_lock(self, target: Target) -> None:
        """Called once when the lock transitions from unlocked to locked for a target."""

    def on_lock_lost(self, target: Optional[Target]) -> None:
        """Called when a previously locked target is no longer locked."""


@dataclass
class LockOnControllerLink:
    """Bridge ``LockOnSystem`` updates into a missile ``MainController`` interface."""

    controller: MissileMainController
    lock_on: LockOnSystem = field(default_factory=LockOnSystem)
    _last_state: LockState = field(default_factory=LockState, init=False)

    def _target_changed(self, new: Optional[Target], previous: Optional[Target]) -> bool:
        if new is None and previous is None:
            return False
        if new is None or previous is None:
            return True
        return new.identifier != previous.identifier

    def step(
        self, origin: Vector3, aim: Vector3, targets: Iterable[Target], dt: float
    ) -> LockState:
        """Advance the lock-on system and notify the controller of state changes."""

        state = self.lock_on.update(origin, aim, targets, dt)
        previous = self._last_state

        if self._target_changed(state.target, previous.target):
            self.controller.set_tracking_target(state.target)

        if not previous.locked and state.locked and state.target:
            self.controller.on_lock(state.target)
        elif previous.locked and not state.locked:
            self.controller.on_lock_lost(previous.target)
            if state.target is None:
                self.controller.set_tracking_target(None)

        self._last_state = self.lock_on.status()
        return state
