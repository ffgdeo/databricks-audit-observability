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
-- ============================================================

-- Sales: Customers
CREATE OR REPLACE TABLE ${var.catalog}.sales_data.customers AS
SELECT
  id AS customer_id,
  CONCAT('Customer_', CAST(id AS STRING)) AS name,
  CONCAT('customer', CAST(id AS STRING), '@example.com') AS email,
  CASE WHEN id % 4 = 0 THEN 'Enterprise' WHEN id % 4 = 1 THEN 'Mid-Market' WHEN id % 4 = 2 THEN 'SMB' ELSE 'Startup' END AS segment,
  CASE WHEN id % 5 = 0 THEN 'US-West' WHEN id % 5 = 1 THEN 'US-East' WHEN id % 5 = 2 THEN 'EMEA' WHEN id % 5 = 3 THEN 'APAC' ELSE 'LATAM' END AS region,
  DATE_ADD('2023-01-01', CAST(FLOOR(RAND(id) * 730) AS INT)) AS created_date
FROM RANGE(500) AS t(id);

-- Sales: Orders
CREATE OR REPLACE TABLE ${var.catalog}.sales_data.orders AS
SELECT
  id AS order_id,
  CAST(FLOOR(RAND(id) * 500) AS INT) AS customer_id,
  DATE_ADD('2024-01-01', CAST(FLOOR(RAND(id + 1) * 430) AS INT)) AS order_date,
  ROUND(50 + RAND(id + 2) * 9950, 2) AS amount,
  CASE WHEN id % 5 = 0 THEN 'US-West' WHEN id % 5 = 1 THEN 'US-East' WHEN id % 5 = 2 THEN 'EMEA' WHEN id % 5 = 3 THEN 'APAC' ELSE 'LATAM' END AS region,
  CASE WHEN RAND(id + 3) > 0.15 THEN 'completed' WHEN RAND(id + 3) > 0.05 THEN 'pending' ELSE 'cancelled' END AS status,
  CASE WHEN id % 3 = 0 THEN 'Platform License' WHEN id % 3 = 1 THEN 'Professional Services' ELSE 'Training' END AS product_category
FROM RANGE(5000) AS t(id);

-- Marketing: Campaigns
CREATE OR REPLACE TABLE ${var.catalog}.marketing_data.campaigns AS
SELECT
  id AS campaign_id,
  CONCAT('Campaign_', CAST(id AS STRING)) AS name,
  CASE WHEN id % 4 = 0 THEN 'Email' WHEN id % 4 = 1 THEN 'Paid Search' WHEN id % 4 = 2 THEN 'Social Media' ELSE 'Webinar' END AS channel,
  ROUND(1000 + RAND(id) * 49000, 2) AS spend,
  DATE_ADD('2024-01-01', CAST(FLOOR(RAND(id + 1) * 365) AS INT)) AS start_date,
  DATE_ADD('2024-01-01', CAST(FLOOR(RAND(id + 1) * 365) + 14 + FLOOR(RAND(id + 2) * 60) AS INT)) AS end_date,
  CASE WHEN RAND(id + 3) > 0.3 THEN 'active' ELSE 'completed' END AS status
FROM RANGE(100) AS t(id);

-- Marketing: Leads
CREATE OR REPLACE TABLE ${var.catalog}.marketing_data.leads AS
SELECT
  id AS lead_id,
  CAST(FLOOR(RAND(id) * 100) AS INT) AS campaign_id,
  CONCAT('Lead_', CAST(id AS STRING)) AS name,
  CONCAT('lead', CAST(id AS STRING), '@prospect.com') AS email,
  CAST(FLOOR(RAND(id + 1) * 100) AS INT) AS score,
  CASE WHEN id % 3 = 0 THEN 'Qualified' WHEN id % 3 = 1 THEN 'Nurturing' ELSE 'New' END AS stage,
  DATE_ADD('2024-01-01', CAST(FLOOR(RAND(id + 2) * 430) AS INT)) AS created_date
FROM RANGE(2000) AS t(id);

-- Finance: Transactions
CREATE OR REPLACE TABLE ${var.catalog}.finance_data.transactions AS
SELECT
  id AS txn_id,
  CONCAT('ACC-', LPAD(CAST(FLOOR(RAND(id) * 200) AS STRING), 4, '0')) AS account_id,
  DATE_ADD('2024-01-01', CAST(FLOOR(RAND(id + 1) * 430) AS INT)) AS txn_date,
  ROUND(CASE WHEN RAND(id + 2) > 0.5 THEN RAND(id + 3) * 50000 ELSE -RAND(id + 3) * 25000 END, 2) AS amount,
  CASE WHEN id % 6 = 0 THEN 'Revenue' WHEN id % 6 = 1 THEN 'COGS' WHEN id % 6 = 2 THEN 'OpEx' WHEN id % 6 = 3 THEN 'CapEx' WHEN id % 6 = 4 THEN 'Payroll' ELSE 'Marketing' END AS category,
  CASE WHEN RAND(id + 2) > 0.5 THEN 'credit' ELSE 'debit' END AS type
FROM RANGE(10000) AS t(id);

-- Finance: Budgets
CREATE OR REPLACE TABLE ${var.catalog}.finance_data.budgets AS
SELECT
  id AS budget_id,
  CASE WHEN id % 5 = 0 THEN 'Engineering' WHEN id % 5 = 1 THEN 'Sales' WHEN id % 5 = 2 THEN 'Marketing' WHEN id % 5 = 3 THEN 'Finance' ELSE 'HR' END AS department,
  CASE WHEN id < 5 THEN 'FY2024' ELSE 'FY2025' END AS fiscal_year,
  ROUND(100000 + RAND(id) * 900000, 2) AS allocated,
  ROUND((100000 + RAND(id) * 900000) * (0.4 + RAND(id + 1) * 0.55), 2) AS spent
FROM RANGE(10) AS t(id);

-- HR: Employees
CREATE OR REPLACE TABLE ${var.catalog}.hr_data.employees AS
SELECT
  id AS employee_id,
  CONCAT('Employee_', CAST(id AS STRING)) AS name,
  CASE WHEN id % 5 = 0 THEN 'Engineering' WHEN id % 5 = 1 THEN 'Sales' WHEN id % 5 = 2 THEN 'Marketing' WHEN id % 5 = 3 THEN 'Finance' ELSE 'HR' END AS department,
  CASE WHEN id % 3 = 0 THEN 'Senior' WHEN id % 3 = 1 THEN 'Mid' ELSE 'Junior' END AS level,
  DATE_ADD('2020-01-01', CAST(FLOOR(RAND(id) * 1800) AS INT)) AS hire_date,
  CASE WHEN RAND(id + 1) > 0.1 THEN 'active' ELSE 'inactive' END AS status
FROM RANGE(300) AS t(id);
