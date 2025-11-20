import unittest

from lock_on_system import LockOnSystem, Target


class LockOnSystemTests(unittest.TestCase):
    def test_picks_target_in_fov_and_range(self):
        system = LockOnSystem(max_range=1000, fov_deg=45, lock_on_time=0.5)
        origin = (0.0, 0.0, 0.0)
        aim = (1.0, 0.0, 0.0)
        targets = [
            Target("off_axis", position=(0.0, 100.0, 0.0), heat_signature=10),
            Target("close", position=(400.0, 0.0, 0.0), heat_signature=5),
            Target("far", position=(900.0, 0.0, 0.0), heat_signature=50),
        ]

        state = system.update(origin, aim, targets, dt=0.25)
        self.assertEqual(state.target.identifier, "close")
        self.assertFalse(state.locked)

        state = system.update(origin, aim, targets, dt=0.25)
        self.assertTrue(state.locked)
        self.assertEqual(state.target.identifier, "close")

    def test_requires_time_to_lock(self):
        system = LockOnSystem(lock_on_time=1.0)
        origin = (0.0, 0.0, 0.0)
        aim = (0.0, 1.0, 0.0)
        target = Target("slow_lock", position=(0.0, 500.0, 0.0))

        state = system.update(origin, aim, [target], dt=0.5)
        self.assertFalse(state.locked)
        self.assertLess(state.progress, system.lock_on_time)

        state = system.update(origin, aim, [target], dt=0.5)
        self.assertTrue(state.locked)
        self.assertAlmostEqual(state.progress, system.lock_on_time)

    def test_forgets_target_after_losing_sight(self):
        system = LockOnSystem(lock_on_time=0.2, lost_lock_timeout=0.3)
        origin = (0.0, 0.0, 0.0)
        aim = (1.0, 0.0, 0.0)
        target = Target("evader", position=(100.0, 0.0, 0.0))

        system.update(origin, aim, [target], dt=0.2)
        system.update(origin, aim, [target], dt=0.2)
        self.assertTrue(system.status().locked)

        system.update(origin, aim, [], dt=0.15)
        self.assertTrue(system.status().locked)

        system.update(origin, aim, [], dt=0.2)
        self.assertFalse(system.status().locked)
        self.assertIsNone(system.status().target)

    def test_scores_by_heat_over_distance(self):
        system = LockOnSystem(max_range=1500, fov_deg=60, lock_on_time=0.1)
        origin = (0.0, 0.0, 0.0)
        aim = (1.0, 0.0, 0.0)
        hot_far = Target("hot_far", position=(1200.0, 0.0, 0.0), heat_signature=40)
        warm_close = Target("warm_close", position=(300.0, 0.0, 0.0), heat_signature=5)

        state = system.update(origin, aim, [hot_far, warm_close], dt=0.1)
        self.assertEqual(state.target.identifier, "warm_close")

    def test_predicted_position_uses_velocity(self):
        target = Target("moving", position=(10.0, 0.0, 0.0), velocity=(5.0, 0.0, 0.0))
        predicted = target.predicted_position(2.0)
        self.assertEqual(predicted, (20.0, 0.0, 0.0))

    def test_out_of_fov_is_ignored(self):
        system = LockOnSystem(fov_deg=30)
        origin = (0.0, 0.0, 0.0)
        aim = (1.0, 0.0, 0.0)
        target = Target("side", position=(0.0, 100.0, 0.0))

        state = system.update(origin, aim, [target], dt=0.5)
        self.assertIsNone(state.target)
        self.assertFalse(state.locked)


if __name__ == "__main__":
    unittest.main()
