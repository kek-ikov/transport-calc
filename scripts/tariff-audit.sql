-- Read-only checks. Missing directions are reported, never invented.
SELECT count(*) AS cities_without_coordinates FROM cities WHERE latitude IS NULL OR longitude IS NULL;
SELECT name AS region_without_zone FROM federal_subjects WHERE tariff_zone_id IS NULL;
SELECT d.name AS direction_without_price FROM tariff_directions d WHERE NOT EXISTS (SELECT 1 FROM tariffs t WHERE t.direction_id=d.id);
SELECT min_distance_km,max_distance_km,max_length_mm,max_width_mm,max_height_mm,max_weight_tons,comment FROM fixed_distance_tariffs WHERE source_version='regional-20261117' AND fixed_price IS NULL ORDER BY min_distance_km,max_weight_tons;
SELECT a.id,b.id FROM tariffs a JOIN tariffs b ON a.id<b.id AND a.direction_id=b.direction_id AND a.cargo_size_category_id=b.cargo_size_category_id AND a.min_weight_tons<b.max_weight_tons AND b.min_weight_tons<a.max_weight_tons AND a.min_distance_km<=coalesce(b.max_distance_km,1e9) AND b.min_distance_km<=coalesce(a.max_distance_km,1e9);
