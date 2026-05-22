-- Migration 002: add utm_trax_id to marketplace_orders for strict attribution
-- Run via: clickhouse-client --query "$(cat 002_add_utm_trax_id.sql)"

ALTER TABLE marketplace_orders
    ADD COLUMN IF NOT EXISTS utm_trax_id String DEFAULT '';

-- Index for fast strict attribution lookup
ALTER TABLE marketplace_orders
    ADD INDEX IF NOT EXISTS idx_utm_trax_id (utm_trax_id) TYPE bloom_filter(0.01) GRANULARITY 1;
