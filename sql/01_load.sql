-- Load the three source tables. Run from the repo root.
CREATE OR REPLACE TABLE trials AS SELECT * FROM read_csv_auto('data/trials.csv');
CREATE OR REPLACE TABLE trial_events AS SELECT * FROM read_csv_auto('data/trial_events.csv');
CREATE OR REPLACE TABLE trial_outcomes AS SELECT * FROM read_csv_auto('data/trial_outcomes.csv');
