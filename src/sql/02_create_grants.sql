-- ============================================================
-- Set up grants to simulate multi-team access patterns
-- ============================================================

-- Create groups (these may already exist or need SCIM API)
-- For demo purposes, grant directly to placeholder user accounts

-- Sales schema: analysts can read, engineers can read/write
GRANT USE SCHEMA ON SCHEMA ${var.catalog}.sales_data TO `data-analysts`;
GRANT SELECT ON SCHEMA ${var.catalog}.sales_data TO `data-analysts`;
GRANT USE SCHEMA ON SCHEMA ${var.catalog}.sales_data TO `data-engineers`;
GRANT ALL PRIVILEGES ON SCHEMA ${var.catalog}.sales_data TO `data-engineers`;
GRANT USE SCHEMA ON SCHEMA ${var.catalog}.sales_data TO `finance-team`;
GRANT SELECT ON SCHEMA ${var.catalog}.sales_data TO `finance-team`;

-- Marketing schema: broad read access
GRANT USE SCHEMA ON SCHEMA ${var.catalog}.marketing_data TO `data-analysts`;
GRANT SELECT ON SCHEMA ${var.catalog}.marketing_data TO `data-analysts`;
GRANT USE SCHEMA ON SCHEMA ${var.catalog}.marketing_data TO `data-engineers`;
GRANT SELECT ON SCHEMA ${var.catalog}.marketing_data TO `data-engineers`;

-- Finance schema: restricted to finance team + read-only for analysts
GRANT USE SCHEMA ON SCHEMA ${var.catalog}.finance_data TO `finance-team`;
GRANT ALL PRIVILEGES ON SCHEMA ${var.catalog}.finance_data TO `finance-team`;
GRANT USE SCHEMA ON SCHEMA ${var.catalog}.finance_data TO `data-analysts`;
GRANT SELECT ON SCHEMA ${var.catalog}.finance_data TO `data-analysts`;

-- HR schema: restricted
GRANT USE SCHEMA ON SCHEMA ${var.catalog}.hr_data TO `hr-team`;
GRANT ALL PRIVILEGES ON SCHEMA ${var.catalog}.hr_data TO `hr-team`;
