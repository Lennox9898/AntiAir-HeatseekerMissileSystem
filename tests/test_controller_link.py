import unittest

from lock_on_system import (
    LockOnControllerLink,
    LockOnSystem,
    MissileMainController,
    Target,
)


class FakeMainController(MissileMainController):
    def __init__(self):
        self.tracking_updates = []
        self.lock_events = []
        self.lock_loss_events = []

    def set_tracking_target(self, target):
        self.tracking_updates.append(target.identifier if target else None)

    def on_lock(self, target):
        self.lock_events.append(target.identifier)

    def on_lock_lost(self, target):
        self.lock_loss_events.append(target.identifier if target else None)


class LockOnControllerLinkTests(unittest.TestCase):
    def test_notifies_controller_on_lock_and_loss(self):
        controller = FakeMainController()
        link = LockOnControllerLink(
            controller=controller,
            lock_on=LockOnSystem(lock_on_time=0.2, lost_lock_timeout=0.1),
        )

        origin = (0.0, 0.0, 0.0)
        aim = (1.0, 0.0, 0.0)
        target = Target("bomber", position=(500.0, 0.0, 0.0))

        link.step(origin, aim, [target], dt=0.1)
        self.assertEqual(controller.tracking_updates, ["bomber"])
        self.assertEqual(controller.lock_events, [])

        link.step(origin, aim, [target], dt=0.1)
        self.assertEqual(controller.lock_events, ["bomber"])

        link.step(origin, aim, [], dt=0.15)
        self.assertEqual(controller.lock_loss_events, ["bomber"])
        self.assertEqual(controller.tracking_updates[-1], None)

    def test_updates_controller_when_target_changes(self):
        controller = FakeMainController()
        link = LockOnControllerLink(controller=controller, lock_on=LockOnSystem(lock_on_time=0.2))

        origin = (0.0, 0.0, 0.0)
        aim = (1.0, 0.0, 0.0)
        first = Target("scout", position=(300.0, 0.0, 0.0))
        second = Target("fighter", position=(200.0, 0.0, 0.0))

        link.step(origin, aim, [first], dt=0.05)
        link.step(origin, aim, [second], dt=0.05)

        self.assertEqual(controller.tracking_updates, ["scout", "fighter"])


if __name__ == "__main__":
    unittest.main()
