import unittest
from unittest.mock import Mock, patch
from types import SimpleNamespace as Obj
from decimal import Decimal
from app.services import calculator as c

class OptimizationTests(unittest.TestCase):
    def test_reverse_cache_is_not_reused(self):
        db = Mock()
        db.execute.return_value.scalar_one_or_none.return_value = None
        with patch.object(c, "get_distance_from_osrm", return_value=(Decimal("12.3"), 15)) as route:
            result = c.get_or_create_distance_cache(db, Obj(id=1, latitude=1, longitude=2), Obj(id=2, latitude=3, longitude=4))
        self.assertEqual(db.execute.call_count, 1)
        route.assert_called_once()
        self.assertEqual(result.from_location_id, 1)
        self.assertEqual(result.to_location_id, 2)

    def test_direction_priority_preserved(self):
        db = Mock()
        preferred = Obj(from_tariff_zone_id=2, to_tariff_zone_id=4)
        db.scalars.return_value.all.return_value = [Obj(from_tariff_zone_id=1, to_tariff_zone_id=3), preferred]
        result = c.find_zone_to_zone_direction(db, [Obj(id=2), Obj(id=1)], [Obj(id=4), Obj(id=3)])
        self.assertIs(result[0], preferred)
        db.scalars.assert_called_once()

    def test_grid_loaded_once(self):
        c.load_regional_rates.cache_clear()
        self.assertIs(c.load_regional_rates(), c.load_regional_rates())
        self.assertEqual(len(c.load_regional_rates()), 144)

if __name__ == "__main__": unittest.main()
