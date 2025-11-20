"""Lock-on system utilities for selecting and tracking targets.

This module implements a simple, dependency-free lock-on algorithm that
can be reused by simulations or prototypes that need to pick targets
within a field of view and maintain a lock while targets are visible.
"""

from .lock_on import Target, LockOnSystem, LockState, Vector3
from .controller_link import LockOnControllerLink, MissileMainController
from .missile_core import EngineModule, EngineReport, MissileCore, RadarModule

__all__ = [
    "Target",
    "LockOnSystem",
    "LockState",
    "Vector3",
    "LockOnControllerLink",
    "MissileMainController",
    "MissileCore",
    "RadarModule",
    "EngineModule",
    "EngineReport",
]
