CREATE TABLE IF NOT EXISTS review(
        "_id"                     TEXT    PRIMARY KEY
    ,   "brand"                   TEXT
    ,   "model"                   TEXT
    ,   "production_year"         INT
    ,   "policy_holder_name"      TEXT
    ,   "address"                 TEXT
    ,   "post_code"               TEXT
    ,   "state"                   TEXT
    ,   "city"                    TEXT
    ,   "country"                 TEXT
    ,   "currency"                VARCHAR(3)
    ,   "total_cost"              NUMERIC
    ,   "time_of_accident"        TIMESTAMP
    ,   "estimate"                JSONB
    ,   "raw"                     JSONB
);

CREATE INDEX IF NOT EXISTS car_mm_idx ON review (brand, model, production_year);
CREATE INDEX IF NOT EXISTS address_mm_idx ON review (country, state);
CREATE INDEX IF NOT EXISTS  currency_idx ON review (currency);
CREATE INDEX IF NOT EXISTS review_estimate_gin_idx ON review USING  gin (estimate jsonb_path_ops);
