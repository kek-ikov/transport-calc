BEGIN;
CREATE INDEX IF NOT EXISTS idx_distance_cache_direction ON distance_cache(from_location_id, to_location_id);
COMMIT;
