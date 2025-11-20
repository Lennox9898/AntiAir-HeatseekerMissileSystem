import unittest

from lock_on_system import (
    EngineModule,
    EngineReport,
    MissileCore,
    RadarModule,
    Vector3,
)


class DummyRadar(RadarModule):
    def __init__(self) -> None:
        self.updates: list[tuple[Vector3, Vector3]] = []

    def on_course_update(self, position: Vector3, heading: Vector3) -> None:
        self.updates.append((position, heading))


class DummyEngine(EngineModule):
    def __init__(self, remaining: float, capacity: float, consumption: float) -> None:
        self._remaining = remaining
        self._capacity = capacity
        self._consumption = consumption

    def fuel_remaining(self) -> float:
        return self._remaining

    def fuel_capacity(self) -> float:
        return self._capacity

    def current_fuel_consumption(self) -> float:
        return self._consumption


class MissileCoreTests(unittest.TestCase):
    def test_steering_notifies_radar(self) -> None:
        radar = DummyRadar()
        core = MissileCore(position=(0.0, 0.0, 0.0))

        core.connect_radar(radar)
        core.steer((0.0, 1.0, 0.0))
        core.relocate((10.0, 0.0, 0.0))

        self.assertGreaterEqual(len(radar.updates), 3)
        self.assertEqual(radar.updates[0][0], (0.0, 0.0, 0.0))
        self.assertEqual(radar.updates[1][1], (0.0, 1.0, 0.0))
        self.assertEqual(radar.updates[-1][0], (10.0, 0.0, 0.0))

    def test_engine_report_exposes_reserve_time(self) -> None:
        engine = DummyEngine(remaining=50.0, capacity=100.0, consumption=5.0)
        core = MissileCore(engine=engine)

        report = core.engine_report()
        self.assertIsInstance(report, EngineReport)
        self.assertEqual(report.fuel_remaining, 50.0)
        self.assertEqual(report.fuel_capacity, 100.0)
        self.assertEqual(report.consumption_rate, 5.0)
        self.assertAlmostEqual(report.reserve_seconds, 10.0)

    def test_engine_report_handles_zero_consumption(self) -> None:
        engine = DummyEngine(remaining=20.0, capacity=100.0, consumption=0.0)
        core = MissileCore(engine=engine)

        report = core.engine_report()
        self.assertIsNone(report.reserve_seconds)

    def test_engine_report_requires_connection(self) -> None:
        core = MissileCore()
        with self.assertRaises(RuntimeError):
            core.engine_report()


if __name__ == "__main__":
    unittest.main()
