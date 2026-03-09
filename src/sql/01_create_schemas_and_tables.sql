-- ============================================================
-- Step 1: Create schemas with business_owner tags
-- ============================================================

CREATE SCHEMA IF NOT EXISTS ${var.catalog}.sales_data
COMMENT 'Sales orders, customers, and revenue data';

ALTER SCHEMA ${var.catalog}.sales_data SET TAGS ('business_owner' = 'alice.johnson@acme.com');

CREATE SCHEMA IF NOT EXISTS ${var.catalog}.marketing_data
COMMENT 'Campaign performance and lead generation data';

ALTER SCHEMA ${var.catalog}.marketing_data SET TAGS ('business_owner' = 'bob.smith@acme.com');

CREATE SCHEMA IF NOT EXISTS ${var.catalog}.finance_data
COMMENT 'Financial transactions and budget tracking';

ALTER SCHEMA ${var.catalog}.finance_data SET TAGS ('business_owner' = 'alice.johnson@acme.com');

CREATE SCHEMA IF NOT EXISTS ${var.catalog}.hr_data
COMMENT 'Employee records and workforce analytics';

ALTER SCHEMA ${var.catalog}.hr_data SET TAGS ('business_owner' = 'carol.davis@acme.com');

-- ============================================================
-- Step 2: Create tables with realistic sample data
-- Using HASH() and modulo for deterministic pseudo-random values
-- ============================================================

-- Sales: Customers
CREATE OR REPLACE TABLE ${var.catalog}.sales_data.customers AS
SELECT
  id AS customer_id,
  CONCAT('Customer_', CAST(id AS STRING)) AS name,
  CONCAT('customer', CAST(id AS STRING), '@example.com') AS email,
  CASE WHEN id % 4 = 0 THEN 'Enterprise' WHEN id % 4 = 1 THEN 'Mid-Market' WHEN id % 4 = 2 THEN 'SMB' ELSE 'Startup' END AS segment,
  CASE WHEN id % 5 = 0 THEN 'US-West' WHEN id % 5 = 1 THEN 'US-East' WHEN id % 5 = 2 THEN 'EMEA' WHEN id % 5 = 3 THEN 'APAC' ELSE 'LATAM' END AS region,
  DATE_ADD('2023-01-01', CAST(ABS(HASH(id)) % 730 AS INT)) AS created_date
FROM RANGE(500) AS t(id);

-- Sales: Orders
CREATE OR REPLACE TABLE ${var.catalog}.sales_data.orders AS
SELECT
  id AS order_id,
  ABS(HASH(id)) % 500 AS customer_id,
  DATE_ADD('2024-01-01', CAST(ABS(HASH(id + 1000)) % 430 AS INT)) AS order_date,
  ROUND(50 + (ABS(HASH(id + 2000)) % 9950), 2) AS amount,
  CASE WHEN id % 5 = 0 THEN 'US-West' WHEN id % 5 = 1 THEN 'US-East' WHEN id % 5 = 2 THEN 'EMEA' WHEN id % 5 = 3 THEN 'APAC' ELSE 'LATAM' END AS region,
  CASE WHEN id % 7 < 5 THEN 'completed' WHEN id % 7 < 6 THEN 'pending' ELSE 'cancelled' END AS status,
  CASE WHEN id % 3 = 0 THEN 'Platform License' WHEN id % 3 = 1 THEN 'Professional Services' ELSE 'Training' END AS product_category
FROM RANGE(5000) AS t(id);

-- Marketing: Campaigns
CREATE OR REPLACE TABLE ${var.catalog}.marketing_data.campaigns AS
SELECT
  id AS campaign_id,
  CONCAT('Campaign_', CAST(id AS STRING)) AS name,
  CASE WHEN id % 4 = 0 THEN 'Email' WHEN id % 4 = 1 THEN 'Paid Search' WHEN id % 4 = 2 THEN 'Social Media' ELSE 'Webinar' END AS channel,
  ROUND(1000 + (ABS(HASH(id)) % 49000), 2) AS spend,
  DATE_ADD('2024-01-01', CAST(ABS(HASH(id + 100)) % 365 AS INT)) AS start_date,
  DATE_ADD('2024-01-01', CAST(ABS(HASH(id + 100)) % 365 + 14 + ABS(HASH(id + 200)) % 60 AS INT)) AS end_date,
  CASE WHEN id % 3 > 0 THEN 'active' ELSE 'completed' END AS status
FROM RANGE(100) AS t(id);

-- Marketing: Leads
CREATE OR REPLACE TABLE ${var.catalog}.marketing_data.leads AS
SELECT
  id AS lead_id,
  ABS(HASH(id)) % 100 AS campaign_id,
  CONCAT('Lead_', CAST(id AS STRING)) AS name,
  CONCAT('lead', CAST(id AS STRING), '@prospect.com') AS email,
  ABS(HASH(id + 500)) % 100 AS score,
  CASE WHEN id % 3 = 0 THEN 'Qualified' WHEN id % 3 = 1 THEN 'Nurturing' ELSE 'New' END AS stage,
  DATE_ADD('2024-01-01', CAST(ABS(HASH(id + 600)) % 430 AS INT)) AS created_date
FROM RANGE(2000) AS t(id);

-- Finance: Transactions
CREATE OR REPLACE TABLE ${var.catalog}.finance_data.transactions AS
SELECT
  id AS txn_id,
  CONCAT('ACC-', LPAD(CAST(ABS(HASH(id)) % 200 AS STRING), 4, '0')) AS account_id,
  DATE_ADD('2024-01-01', CAST(ABS(HASH(id + 1000)) % 430 AS INT)) AS txn_date,
  ROUND(CASE WHEN id % 2 = 0 THEN (ABS(HASH(id + 2000)) % 50000) ELSE -(ABS(HASH(id + 3000)) % 25000) END, 2) AS amount,
  CASE WHEN id % 6 = 0 THEN 'Revenue' WHEN id % 6 = 1 THEN 'COGS' WHEN id % 6 = 2 THEN 'OpEx' WHEN id % 6 = 3 THEN 'CapEx' WHEN id % 6 = 4 THEN 'Payroll' ELSE 'Marketing' END AS category,
  CASE WHEN id % 2 = 0 THEN 'credit' ELSE 'debit' END AS type
FROM RANGE(10000) AS t(id);

-- Finance: Budgets
CREATE OR REPLACE TABLE ${var.catalog}.finance_data.budgets AS
SELECT
  id AS budget_id,
  CASE WHEN id % 5 = 0 THEN 'Engineering' WHEN id % 5 = 1 THEN 'Sales' WHEN id % 5 = 2 THEN 'Marketing' WHEN id % 5 = 3 THEN 'Finance' ELSE 'HR' END AS department,
  CASE WHEN id < 5 THEN 'FY2024' ELSE 'FY2025' END AS fiscal_year,
  ROUND(100000 + (ABS(HASH(id)) % 900000), 2) AS allocated,
  ROUND((100000 + (ABS(HASH(id)) % 900000)) * (40 + ABS(HASH(id + 100)) % 55) / 100.0, 2) AS spent
FROM RANGE(10) AS t(id);

-- HR: Employees
CREATE OR REPLACE TABLE ${var.catalog}.hr_data.employees AS
SELECT
  id AS employee_id,
  CONCAT('Employee_', CAST(id AS STRING)) AS name,
  CASE WHEN id % 5 = 0 THEN 'Engineering' WHEN id % 5 = 1 THEN 'Sales' WHEN id % 5 = 2 THEN 'Marketing' WHEN id % 5 = 3 THEN 'Finance' ELSE 'HR' END AS department,
  CASE WHEN id % 3 = 0 THEN 'Senior' WHEN id % 3 = 1 THEN 'Mid' ELSE 'Junior' END AS level,
  DATE_ADD('2020-01-01', CAST(ABS(HASH(id)) % 1800 AS INT)) AS hire_date,
  CASE WHEN id % 10 > 0 THEN 'active' ELSE 'inactive' END AS status
FROM RANGE(300) AS t(id);
