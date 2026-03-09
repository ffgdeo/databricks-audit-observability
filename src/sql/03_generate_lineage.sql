-- ============================================================
-- Generate lineage by creating derived/aggregate tables
-- These CREATE TABLE AS SELECT statements create lineage edges
-- that will appear in system.access.table_lineage
-- ============================================================

-- Sales: Monthly revenue summary (orders -> order_summary)
CREATE OR REPLACE TABLE ${var.catalog}.sales_data.order_summary AS
SELECT
  region,
  DATE_TRUNC('month', order_date) AS month,
  product_category,
  COUNT(*) AS order_count,
  SUM(amount) AS total_revenue,
  AVG(amount) AS avg_order_value,
  SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) AS completed_orders,
  SUM(CASE WHEN status = 'cancelled' THEN 1 ELSE 0 END) AS cancelled_orders
FROM ${var.catalog}.sales_data.orders
GROUP BY region, DATE_TRUNC('month', order_date), product_category;

-- Sales: Customer lifetime value (customers + orders -> customer_ltv)
CREATE OR REPLACE TABLE ${var.catalog}.sales_data.customer_ltv AS
SELECT
  c.customer_id,
  c.name,
  c.segment,
  c.region,
  COUNT(o.order_id) AS total_orders,
  COALESCE(SUM(o.amount), 0) AS lifetime_value,
  MIN(o.order_date) AS first_order_date,
  MAX(o.order_date) AS last_order_date
FROM ${var.catalog}.sales_data.customers c
LEFT JOIN ${var.catalog}.sales_data.orders o ON c.customer_id = o.customer_id
GROUP BY c.customer_id, c.name, c.segment, c.region;

-- Marketing: Campaign ROI (campaigns + leads -> campaign_roi)
CREATE OR REPLACE TABLE ${var.catalog}.marketing_data.campaign_roi AS
SELECT
  c.campaign_id,
  c.name AS campaign_name,
  c.channel,
  c.spend,
  COUNT(l.lead_id) AS total_leads,
  SUM(CASE WHEN l.stage = 'Qualified' THEN 1 ELSE 0 END) AS qualified_leads,
  ROUND(c.spend / NULLIF(COUNT(l.lead_id), 0), 2) AS cost_per_lead
FROM ${var.catalog}.marketing_data.campaigns c
LEFT JOIN ${var.catalog}.marketing_data.leads l ON c.campaign_id = l.campaign_id
GROUP BY c.campaign_id, c.name, c.channel, c.spend;

-- Finance: Budget vs Actual by department (transactions + budgets -> budget_variance)
CREATE OR REPLACE TABLE ${var.catalog}.finance_data.budget_variance AS
SELECT
  b.department,
  b.fiscal_year,
  b.allocated AS budget_allocated,
  b.spent AS budget_spent,
  COALESCE(t.actual_spend, 0) AS actual_spend,
  b.allocated - COALESCE(t.actual_spend, 0) AS variance,
  ROUND((COALESCE(t.actual_spend, 0) / b.allocated) * 100, 1) AS utilization_pct
FROM ${var.catalog}.finance_data.budgets b
LEFT JOIN (
  SELECT
    category AS department,
    CASE WHEN YEAR(txn_date) = 2024 THEN 'FY2024' ELSE 'FY2025' END AS fiscal_year,
    SUM(ABS(amount)) AS actual_spend
  FROM ${var.catalog}.finance_data.transactions
  WHERE type = 'debit'
  GROUP BY category, CASE WHEN YEAR(txn_date) = 2024 THEN 'FY2024' ELSE 'FY2025' END
) t ON b.department = t.department AND b.fiscal_year = t.fiscal_year;
