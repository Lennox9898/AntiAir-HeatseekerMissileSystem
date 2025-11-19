"""Lock-on system utilities for selecting and tracking targets.

This module implements a simple, dependency-free lock-on algorithm that
can be reused by simulations or prototypes that need to pick targets
within a field of view and maintain a lock while targets are visible.
"""

from .lock_on import Target, LockOnSystem, LockState
 e9ly99-main/add-quick-target-lock-on-system
from .controller_link import LockOnControllerLink, MissileMainController

__all__ = [
    "Target",
    "LockOnSystem",
    "LockState",
    "LockOnControllerLink",
    "MissileMainController",



__all__ = ["Target", "LockOnSystem", "LockState"]
 main
