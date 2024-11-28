
USE kafkapipeline;

CREATE TABLE IF NOT EXISTS spacex_launches (
  launch_id TEXT PRIMARY KEY,
  mission_name TEXT,
  launch_date_utc TIMESTAMP,
  rocket_name TEXT,
  launch_success BOOLEAN,
  site_name TEXT,
  payload_type TEXT,
  payload_mass_kg DOUBLE
);