-- ============================================================
-- NOTE: System schemas must be enabled via REST API, not SQL.
-- Run these commands via Databricks CLI:
--
-- databricks api put /api/2.0/unity-catalog/metastores/<metastore_id>/systemschemas/access
-- databricks api put /api/2.0/unity-catalog/metastores/<metastore_id>/systemschemas/billing
-- databricks api put /api/2.0/unity-catalog/metastores/<metastore_id>/systemschemas/query
--
-- Or use the setup script: ./resources/enable_system_schemas.sh
-- ============================================================

-- Verify system schemas are accessible after enablement:
SELECT 'audit' AS system_table, COUNT(*) AS row_count FROM system.access.audit WHERE event_date >= CURRENT_DATE() - INTERVAL 1 DAY
UNION ALL
SELECT 'table_lineage', COUNT(*) FROM system.access.table_lineage WHERE event_date >= CURRENT_DATE() - INTERVAL 1 DAY;
