#!/usr/bin/env python3
"""
Build the Audit & Observability Lakeview dashboard JSON.
Outputs the serialized_dashboard JSON to stdout or to a file.

Usage:
    python3 build_dashboard.py > dashboard.lvdash.json
    python3 build_dashboard.py --catalog my_catalog > dashboard.lvdash.json
"""

import json
import sys
import uuid
import argparse


def gen_id():
    return uuid.uuid4().hex[:8]


def build_dashboard(catalog: str = "audit_observability_catalog") -> dict:
    datasets = []
    pages = []

    # ================================================================
    # DATASETS — each query is a SINGLE string to avoid join issues
    # ================================================================

    # DS1: Schemas by business owner (from tags)
    datasets.append({
        "name": "ds_my_schemas",
        "displayName": "My Schemas",
        "queryLines": [
            f"SELECT st.catalog_name, st.schema_name, st.tag_value AS business_owner, s.comment AS schema_description, s.created AS schema_created, (SELECT COUNT(*) FROM system.information_schema.tables t WHERE t.table_catalog = st.catalog_name AND t.table_schema = st.schema_name AND t.table_type IN ('MANAGED', 'EXTERNAL')) AS table_count FROM system.information_schema.schema_tags st JOIN system.information_schema.schemata s ON st.catalog_name = s.catalog_name AND st.schema_name = s.schema_name WHERE st.tag_name = 'business_owner'"
        ]
    })

    # DS2: Permissions on schemas
    datasets.append({
        "name": "ds_permissions",
        "displayName": "Schema Permissions",
        "queryLines": [
            f"SELECT sp.schema_name, sp.grantee, sp.privilege_type, sp.grantor, sp.is_grantable, sp.inherited_from, st.tag_value AS business_owner FROM system.information_schema.schema_privileges sp JOIN system.information_schema.schema_tags st ON sp.catalog_name = st.catalog_name AND sp.schema_name = st.schema_name WHERE st.tag_name = 'business_owner'"
        ]
    })

    # DS3: Data freshness
    datasets.append({
        "name": "ds_freshness",
        "displayName": "Data Freshness",
        "queryLines": [
            f"SELECT t.table_catalog, t.table_schema, t.table_name, t.table_type, t.last_altered, t.last_altered_by, DATEDIFF(HOUR, t.last_altered, CURRENT_TIMESTAMP()) AS hours_since_update, CASE WHEN DATEDIFF(HOUR, t.last_altered, CURRENT_TIMESTAMP()) < 24 THEN 'Fresh' WHEN DATEDIFF(HOUR, t.last_altered, CURRENT_TIMESTAMP()) < 72 THEN 'Stale' ELSE 'Critical' END AS freshness_status, st.tag_value AS business_owner FROM system.information_schema.tables t JOIN system.information_schema.schema_tags st ON t.table_catalog = st.catalog_name AND t.table_schema = st.schema_name WHERE st.tag_name = 'business_owner' AND t.table_type IN ('MANAGED', 'EXTERNAL') ORDER BY t.last_altered DESC"
        ]
    })

    # DS4: Audit trail — filter to our catalog for relevance
    datasets.append({
        "name": "ds_audit",
        "displayName": "Audit Trail",
        "queryLines": [
            f"SELECT a.event_time, a.event_date, a.user_identity.email AS user_email, a.action_name, COALESCE(a.request_params.full_name_arg, a.request_params.name) AS object_accessed, a.service_name, a.source_ip_address, a.response.status_code AS status_code FROM system.access.audit a WHERE a.service_name = 'unityCatalog' AND a.action_name IN ('getTable', 'createTable', 'deleteTable', 'getSchema', 'createSchema', 'alterSchema', 'generateTemporaryTableCredential', 'updatePermissions', 'getPermissions') AND a.event_date >= DATEADD(DAY, -30, CURRENT_DATE()) ORDER BY a.event_time DESC LIMIT 1000"
        ]
    })

    # DS5: Table lineage
    datasets.append({
        "name": "ds_lineage",
        "displayName": "Table Lineage",
        "queryLines": [
            f"SELECT tl.source_table_full_name, tl.target_table_full_name, tl.source_table_catalog, tl.source_table_schema, tl.target_table_catalog, tl.target_table_schema, tl.entity_type, tl.event_time FROM system.access.table_lineage tl WHERE (tl.source_table_full_name LIKE '{catalog}.%' OR tl.target_table_full_name LIKE '{catalog}.%') AND tl.event_date >= DATEADD(DAY, -30, CURRENT_DATE()) ORDER BY tl.event_time DESC LIMIT 500"
        ]
    })

    # DS6: Query activity by user — fixed column name: execution_status not status
    datasets.append({
        "name": "ds_query_activity",
        "displayName": "Query Activity",
        "queryLines": [
            f"SELECT qh.executed_by AS user_name, DATE_TRUNC('DAY', qh.start_time) AS query_date, COUNT(*) AS query_count, SUM(qh.total_duration_ms) / 1000.0 AS total_duration_secs, SUM(qh.read_rows) AS total_rows_read FROM system.query.history qh WHERE qh.start_time >= DATEADD(DAY, -30, CURRENT_DATE()) AND qh.statement_text LIKE '%{catalog}%' AND qh.execution_status = 'FINISHED' GROUP BY qh.executed_by, DATE_TRUNC('DAY', qh.start_time) ORDER BY query_date DESC"
        ]
    })

    # DS7: Consumption/billing
    datasets.append({
        "name": "ds_consumption",
        "displayName": "DBU Consumption",
        "queryLines": [
            f"SELECT u.usage_date, u.sku_name, u.billing_origin_product, SUM(u.usage_quantity) AS total_dbus FROM system.billing.usage u WHERE u.usage_date >= DATEADD(DAY, -30, CURRENT_DATE()) GROUP BY u.usage_date, u.sku_name, u.billing_origin_product ORDER BY u.usage_date DESC"
        ]
    })

    # ================================================================
    # PAGE 1: Ownership & Governance Overview
    # ================================================================
    p1_id = gen_id()
    p1_layout = []

    # Business Owner filter (dropdown)
    filter_id = gen_id()
    filter_query_name = f"filter_{filter_id}_business_owner"
    p1_layout.append({
        "widget": {
            "name": filter_id,
            "queries": [{
                "name": filter_query_name,
                "query": {
                    "datasetName": "ds_my_schemas",
                    "fields": [
                        {"name": "business_owner", "expression": "`business_owner`"},
                        {"name": "business_owner_associativity", "expression": "COUNT_IF(`associative_filter_predicate_group`)"}
                    ],
                    "disaggregated": False
                }
            }],
            "spec": {
                "version": 2,
                "widgetType": "filter-single-select",
                "encodings": {
                    "fields": [{
                        "fieldName": "business_owner",
                        "displayName": "Business Owner",
                        "queryName": filter_query_name
                    }]
                },
                "frame": {"showTitle": True, "title": "Business Owner"}
            }
        },
        "position": {"x": 0, "y": 0, "width": 2, "height": 2}
    })

    # Counter: Schema Count
    p1_layout.append({
        "widget": {
            "name": gen_id(),
            "queries": [{"name": "main_query", "query": {
                "datasetName": "ds_my_schemas",
                "fields": [{"name": "count(*)", "expression": "COUNT(`*`)"}],
                "disaggregated": True
            }}],
            "spec": {
                "version": 2, "widgetType": "counter",
                "encodings": {"value": {"fieldName": "count(*)", "displayName": "Schemas Owned"}},
                "frame": {"showTitle": True, "title": "Schemas Owned"}
            }
        },
        "position": {"x": 2, "y": 0, "width": 1, "height": 2}
    })

    # Counter: Table Count
    p1_layout.append({
        "widget": {
            "name": gen_id(),
            "queries": [{"name": "main_query", "query": {
                "datasetName": "ds_freshness",
                "fields": [{"name": "count(*)", "expression": "COUNT(`*`)"}],
                "disaggregated": True
            }}],
            "spec": {
                "version": 2, "widgetType": "counter",
                "encodings": {"value": {"fieldName": "count(*)", "displayName": "Total Tables"}},
                "frame": {"showTitle": True, "title": "Total Tables"}
            }
        },
        "position": {"x": 3, "y": 0, "width": 1, "height": 2}
    })

    # Counter: Total Grants
    p1_layout.append({
        "widget": {
            "name": gen_id(),
            "queries": [{"name": "main_query", "query": {
                "datasetName": "ds_permissions",
                "fields": [{"name": "count(*)", "expression": "COUNT(`*`)"}],
                "disaggregated": True
            }}],
            "spec": {
                "version": 2, "widgetType": "counter",
                "encodings": {"value": {"fieldName": "count(*)", "displayName": "Total Grants"}},
                "frame": {"showTitle": True, "title": "Total Grants"}
            }
        },
        "position": {"x": 4, "y": 0, "width": 1, "height": 2}
    })

    # Counter: Freshness Issues
    p1_layout.append({
        "widget": {
            "name": gen_id(),
            "queries": [{"name": "main_query", "query": {
                "datasetName": "ds_freshness",
                "fields": [{"name": "count(*)", "expression": "COUNT_IF(`freshness_status` != 'Fresh')"}],
                "disaggregated": True
            }}],
            "spec": {
                "version": 2, "widgetType": "counter",
                "encodings": {"value": {"fieldName": "count(*)", "displayName": "Freshness Issues"}},
                "frame": {"showTitle": True, "title": "Freshness Issues"}
            }
        },
        "position": {"x": 5, "y": 0, "width": 1, "height": 2}
    })

    # Table: My Schemas
    p1_layout.append({
        "widget": {
            "name": gen_id(),
            "queries": [{"name": "main_query", "query": {
                "datasetName": "ds_my_schemas",
                "fields": [
                    {"name": "catalog_name", "expression": "`catalog_name`"},
                    {"name": "schema_name", "expression": "`schema_name`"},
                    {"name": "business_owner", "expression": "`business_owner`"},
                    {"name": "schema_description", "expression": "`schema_description`"},
                    {"name": "table_count", "expression": "`table_count`"}
                ],
                "disaggregated": True
            }}],
            "spec": {
                "version": 1, "widgetType": "table",
                "encodings": {"columns": [
                    {"fieldName": "catalog_name", "type": "string", "displayAs": "string", "title": "Catalog", "order": 100000},
                    {"fieldName": "schema_name", "type": "string", "displayAs": "string", "title": "Schema", "order": 100001},
                    {"fieldName": "business_owner", "type": "string", "displayAs": "string", "title": "Owner", "order": 100002},
                    {"fieldName": "schema_description", "type": "string", "displayAs": "string", "title": "Description", "order": 100003},
                    {"fieldName": "table_count", "type": "integer", "displayAs": "number", "title": "Tables", "order": 100004, "alignContent": "right"}
                ]},
                "frame": {"showTitle": True, "title": "My Schemas"}
            }
        },
        "position": {"x": 0, "y": 2, "width": 3, "height": 4}
    })

    # Bar chart: Grants by Grantee
    p1_layout.append({
        "widget": {
            "name": gen_id(),
            "queries": [{"name": "main_query", "query": {
                "datasetName": "ds_permissions",
                "fields": [
                    {"name": "grantee", "expression": "`grantee`"},
                    {"name": "count(*)", "expression": "COUNT(`*`)"},
                    {"name": "privilege_type", "expression": "`privilege_type`"}
                ],
                "disaggregated": False
            }}],
            "spec": {
                "version": 3, "widgetType": "bar",
                "encodings": {
                    "x": {"fieldName": "grantee", "scale": {"type": "categorical", "sort": {"by": "y-reversed"}}, "displayName": "Grantee"},
                    "y": {"fieldName": "count(*)", "scale": {"type": "quantitative"}, "displayName": "Number of Grants"},
                    "color": {"fieldName": "privilege_type", "scale": {"type": "categorical"}, "displayName": "Privilege Type"},
                    "label": {"show": True}
                },
                "frame": {"showTitle": True, "title": "Permissions by Grantee"},
                "mark": {"colors": ["#FFAB00", "#00A972", "#FF3621", "#8BCAE7", "#AB4057"]}
            }
        },
        "position": {"x": 3, "y": 2, "width": 3, "height": 4}
    })

    # Table: Permissions detail
    p1_layout.append({
        "widget": {
            "name": gen_id(),
            "queries": [{"name": "main_query", "query": {
                "datasetName": "ds_permissions",
                "fields": [
                    {"name": "schema_name", "expression": "`schema_name`"},
                    {"name": "grantee", "expression": "`grantee`"},
                    {"name": "privilege_type", "expression": "`privilege_type`"},
                    {"name": "grantor", "expression": "`grantor`"},
                    {"name": "is_grantable", "expression": "`is_grantable`"}
                ],
                "disaggregated": True
            }}],
            "spec": {
                "version": 1, "widgetType": "table",
                "encodings": {"columns": [
                    {"fieldName": "schema_name", "type": "string", "displayAs": "string", "title": "Schema", "order": 100000},
                    {"fieldName": "grantee", "type": "string", "displayAs": "string", "title": "Grantee", "order": 100001},
                    {"fieldName": "privilege_type", "type": "string", "displayAs": "string", "title": "Privilege", "order": 100002},
                    {"fieldName": "grantor", "type": "string", "displayAs": "string", "title": "Granted By", "order": 100003},
                    {"fieldName": "is_grantable", "type": "string", "displayAs": "string", "title": "Grantable?", "order": 100004}
                ]},
                "frame": {"showTitle": True, "title": "Permission Details"}
            }
        },
        "position": {"x": 0, "y": 6, "width": 6, "height": 4}
    })

    # Freshness: bar chart by status
    p1_layout.append({
        "widget": {
            "name": gen_id(),
            "queries": [{"name": "main_query", "query": {
                "datasetName": "ds_freshness",
                "fields": [
                    {"name": "freshness_status", "expression": "`freshness_status`"},
                    {"name": "count(*)", "expression": "COUNT(`*`)"}
                ],
                "disaggregated": False
            }}],
            "spec": {
                "version": 3, "widgetType": "bar",
                "encodings": {
                    "x": {"fieldName": "freshness_status", "scale": {"type": "categorical"}, "displayName": "Freshness Status"},
                    "y": {"fieldName": "count(*)", "scale": {"type": "quantitative"}, "displayName": "Table Count"},
                    "color": {"fieldName": "freshness_status", "scale": {"type": "categorical", "mappings": [
                        {"value": "Fresh", "color": "#00A972"},
                        {"value": "Stale", "color": "#FFAB00"},
                        {"value": "Critical", "color": "#FF3621"}
                    ]}, "displayName": "Status"},
                    "label": {"show": True}
                },
                "frame": {"showTitle": True, "title": "Data Freshness Overview"},
                "mark": {"colors": ["#00A972", "#FFAB00", "#FF3621"]}
            }
        },
        "position": {"x": 0, "y": 10, "width": 3, "height": 4}
    })

    # Freshness: detail table
    p1_layout.append({
        "widget": {
            "name": gen_id(),
            "queries": [{"name": "main_query", "query": {
                "datasetName": "ds_freshness",
                "fields": [
                    {"name": "table_schema", "expression": "`table_schema`"},
                    {"name": "table_name", "expression": "`table_name`"},
                    {"name": "last_altered", "expression": "`last_altered`"},
                    {"name": "hours_since_update", "expression": "`hours_since_update`"},
                    {"name": "freshness_status", "expression": "`freshness_status`"},
                    {"name": "last_altered_by", "expression": "`last_altered_by`"}
                ],
                "disaggregated": True
            }}],
            "spec": {
                "version": 1, "widgetType": "table",
                "encodings": {"columns": [
                    {"fieldName": "table_schema", "type": "string", "displayAs": "string", "title": "Schema", "order": 100000},
                    {"fieldName": "table_name", "type": "string", "displayAs": "string", "title": "Table", "order": 100001},
                    {"fieldName": "last_altered", "type": "datetime", "displayAs": "datetime", "title": "Last Updated", "order": 100002, "alignContent": "right"},
                    {"fieldName": "hours_since_update", "type": "integer", "displayAs": "number", "title": "Hours Ago", "order": 100003, "alignContent": "right"},
                    {"fieldName": "freshness_status", "type": "string", "displayAs": "string", "title": "Status", "order": 100004},
                    {"fieldName": "last_altered_by", "type": "string", "displayAs": "string", "title": "Updated By", "order": 100005}
                ]},
                "frame": {"showTitle": True, "title": "Data Freshness Details"}
            }
        },
        "position": {"x": 3, "y": 10, "width": 3, "height": 4}
    })

    pages.append({
        "name": p1_id,
        "displayName": "Ownership & Governance",
        "pageType": "PAGE_TYPE_CANVAS",
        "layout": p1_layout
    })

    # ================================================================
    # PAGE 2: Audit Trail & Access
    # ================================================================
    p2_id = gen_id()
    p2_layout = []

    # Date filter for audit
    date_filter_id = gen_id()
    date_filter_qname = f"filter_{date_filter_id}_event_date"
    p2_layout.append({
        "widget": {
            "name": date_filter_id,
            "queries": [{"name": date_filter_qname, "query": {
                "datasetName": "ds_audit",
                "fields": [
                    {"name": "event_date", "expression": "`event_date`"},
                    {"name": "event_date_associativity", "expression": "COUNT_IF(`associative_filter_predicate_group`)"}
                ],
                "disaggregated": False
            }}],
            "spec": {
                "version": 2, "widgetType": "filter-date-range-picker",
                "encodings": {"fields": [{"fieldName": "event_date", "displayName": "Event Date", "queryName": date_filter_qname}]},
                "frame": {"showTitle": True, "title": "Date Range"}
            }
        },
        "position": {"x": 0, "y": 0, "width": 2, "height": 2}
    })

    # Counter: Total audit events
    p2_layout.append({
        "widget": {
            "name": gen_id(),
            "queries": [{"name": "main_query", "query": {
                "datasetName": "ds_audit",
                "fields": [{"name": "count(*)", "expression": "COUNT(`*`)"}],
                "disaggregated": True
            }}],
            "spec": {
                "version": 2, "widgetType": "counter",
                "encodings": {"value": {"fieldName": "count(*)", "displayName": "Audit Events"}},
                "frame": {"showTitle": True, "title": "Total Audit Events (30d)"}
            }
        },
        "position": {"x": 2, "y": 0, "width": 2, "height": 2}
    })

    # Counter: Unique users
    p2_layout.append({
        "widget": {
            "name": gen_id(),
            "queries": [{"name": "main_query", "query": {
                "datasetName": "ds_audit",
                "fields": [{"name": "count_distinct", "expression": "COUNT(DISTINCT `user_email`)"}],
                "disaggregated": True
            }}],
            "spec": {
                "version": 2, "widgetType": "counter",
                "encodings": {"value": {"fieldName": "count_distinct", "displayName": "Unique Users"}},
                "frame": {"showTitle": True, "title": "Unique Users"}
            }
        },
        "position": {"x": 4, "y": 0, "width": 2, "height": 2}
    })

    # Line chart: Access events over time
    p2_layout.append({
        "widget": {
            "name": gen_id(),
            "queries": [{"name": "main_query", "query": {
                "datasetName": "ds_audit",
                "fields": [
                    {"name": "day(event_time)", "expression": "DATE_TRUNC(\"DAY\", `event_time`)"},
                    {"name": "count(*)", "expression": "COUNT(`*`)"},
                    {"name": "action_name", "expression": "`action_name`"}
                ],
                "disaggregated": False
            }}],
            "spec": {
                "version": 3, "widgetType": "line",
                "encodings": {
                    "x": {"fieldName": "day(event_time)", "scale": {"type": "temporal"}, "displayName": "Date"},
                    "y": {"fieldName": "count(*)", "scale": {"type": "quantitative"}, "displayName": "Event Count"},
                    "color": {"fieldName": "action_name", "scale": {"type": "categorical"}, "displayName": "Action"}
                },
                "frame": {"showTitle": True, "title": "Access Events Over Time"}
            }
        },
        "position": {"x": 0, "y": 2, "width": 6, "height": 4}
    })

    # Bar chart: Top accessing users
    p2_layout.append({
        "widget": {
            "name": gen_id(),
            "queries": [{"name": "main_query", "query": {
                "datasetName": "ds_audit",
                "fields": [
                    {"name": "user_email", "expression": "`user_email`"},
                    {"name": "count(*)", "expression": "COUNT(`*`)"}
                ],
                "disaggregated": False
            }}],
            "spec": {
                "version": 3, "widgetType": "bar",
                "encodings": {
                    "x": {"fieldName": "user_email", "scale": {"type": "categorical", "sort": {"by": "y-reversed"}}, "displayName": "User"},
                    "y": {"fieldName": "count(*)", "scale": {"type": "quantitative"}, "displayName": "Access Count"},
                    "label": {"show": True}
                },
                "frame": {"showTitle": True, "title": "Top Accessing Users"},
                "mark": {"colors": ["#FFAB00"]}
            }
        },
        "position": {"x": 0, "y": 6, "width": 3, "height": 4}
    })

    # Pie chart: Action types distribution
    p2_layout.append({
        "widget": {
            "name": gen_id(),
            "queries": [{"name": "main_query", "query": {
                "datasetName": "ds_audit",
                "fields": [
                    {"name": "count(*)", "expression": "COUNT(`*`)"},
                    {"name": "action_name", "expression": "`action_name`"}
                ],
                "disaggregated": False
            }}],
            "spec": {
                "version": 3, "widgetType": "pie",
                "encodings": {
                    "angle": {"fieldName": "count(*)", "scale": {"type": "quantitative"}, "displayName": "Count"},
                    "color": {"fieldName": "action_name", "scale": {"type": "categorical"}, "displayName": "Action Type"}
                },
                "frame": {"showTitle": True, "title": "Audit Events by Type"}
            }
        },
        "position": {"x": 3, "y": 6, "width": 3, "height": 4}
    })

    # Table: Audit log detail
    p2_layout.append({
        "widget": {
            "name": gen_id(),
            "queries": [{"name": "main_query", "query": {
                "datasetName": "ds_audit",
                "fields": [
                    {"name": "event_time", "expression": "`event_time`"},
                    {"name": "user_email", "expression": "`user_email`"},
                    {"name": "action_name", "expression": "`action_name`"},
                    {"name": "object_accessed", "expression": "`object_accessed`"},
                    {"name": "source_ip_address", "expression": "`source_ip_address`"},
                    {"name": "status_code", "expression": "`status_code`"}
                ],
                "disaggregated": True
            }}],
            "spec": {
                "version": 1, "widgetType": "table",
                "encodings": {"columns": [
                    {"fieldName": "event_time", "type": "datetime", "displayAs": "datetime", "title": "Time", "order": 100000, "alignContent": "right"},
                    {"fieldName": "user_email", "type": "string", "displayAs": "string", "title": "User", "order": 100001},
                    {"fieldName": "action_name", "type": "string", "displayAs": "string", "title": "Action", "order": 100002},
                    {"fieldName": "object_accessed", "type": "string", "displayAs": "string", "title": "Object", "order": 100003},
                    {"fieldName": "source_ip_address", "type": "string", "displayAs": "string", "title": "IP Address", "order": 100004},
                    {"fieldName": "status_code", "type": "string", "displayAs": "string", "title": "Status", "order": 100005}
                ]},
                "frame": {"showTitle": True, "title": "Audit Log Detail"}
            }
        },
        "position": {"x": 0, "y": 10, "width": 6, "height": 5}
    })

    pages.append({
        "name": p2_id,
        "displayName": "Audit Trail & Access",
        "pageType": "PAGE_TYPE_CANVAS",
        "layout": p2_layout
    })

    # ================================================================
    # PAGE 3: Lineage & Usage
    # ================================================================
    p3_id = gen_id()
    p3_layout = []

    # Table: Lineage edges
    p3_layout.append({
        "widget": {
            "name": gen_id(),
            "queries": [{"name": "main_query", "query": {
                "datasetName": "ds_lineage",
                "fields": [
                    {"name": "source_table_full_name", "expression": "`source_table_full_name`"},
                    {"name": "target_table_full_name", "expression": "`target_table_full_name`"},
                    {"name": "entity_type", "expression": "`entity_type`"},
                    {"name": "event_time", "expression": "`event_time`"}
                ],
                "disaggregated": True
            }}],
            "spec": {
                "version": 1, "widgetType": "table",
                "encodings": {"columns": [
                    {"fieldName": "source_table_full_name", "type": "string", "displayAs": "string", "title": "Source Table", "order": 100000},
                    {"fieldName": "target_table_full_name", "type": "string", "displayAs": "string", "title": "Target Table", "order": 100001},
                    {"fieldName": "entity_type", "type": "string", "displayAs": "string", "title": "Entity Type", "order": 100002},
                    {"fieldName": "event_time", "type": "datetime", "displayAs": "datetime", "title": "Event Time", "order": 100003, "alignContent": "right"}
                ]},
                "frame": {"showTitle": True, "title": "Data Lineage"}
            }
        },
        "position": {"x": 0, "y": 0, "width": 6, "height": 5}
    })

    # Bar: Most connected tables (by lineage edges)
    p3_layout.append({
        "widget": {
            "name": gen_id(),
            "queries": [{"name": "main_query", "query": {
                "datasetName": "ds_lineage",
                "fields": [
                    {"name": "target_table_full_name", "expression": "`target_table_full_name`"},
                    {"name": "count(*)", "expression": "COUNT(`*`)"}
                ],
                "disaggregated": False
            }}],
            "spec": {
                "version": 3, "widgetType": "bar",
                "encodings": {
                    "x": {"fieldName": "target_table_full_name", "scale": {"type": "categorical", "sort": {"by": "y-reversed"}}, "displayName": "Target Table"},
                    "y": {"fieldName": "count(*)", "scale": {"type": "quantitative"}, "displayName": "Lineage Edges"},
                    "label": {"show": True}
                },
                "frame": {"showTitle": True, "title": "Most Derived Tables"},
                "mark": {"colors": ["#8BCAE7"]}
            }
        },
        "position": {"x": 0, "y": 5, "width": 3, "height": 4}
    })

    # Pie: Lineage by entity type
    p3_layout.append({
        "widget": {
            "name": gen_id(),
            "queries": [{"name": "main_query", "query": {
                "datasetName": "ds_lineage",
                "fields": [
                    {"name": "count(*)", "expression": "COUNT(`*`)"},
                    {"name": "entity_type", "expression": "`entity_type`"}
                ],
                "disaggregated": False
            }}],
            "spec": {
                "version": 3, "widgetType": "pie",
                "encodings": {
                    "angle": {"fieldName": "count(*)", "scale": {"type": "quantitative"}, "displayName": "Count"},
                    "color": {"fieldName": "entity_type", "scale": {"type": "categorical"}, "displayName": "Entity Type"}
                },
                "frame": {"showTitle": True, "title": "Lineage by Entity Type"}
            }
        },
        "position": {"x": 3, "y": 5, "width": 3, "height": 4}
    })

    # Line: DBU consumption over time
    p3_layout.append({
        "widget": {
            "name": gen_id(),
            "queries": [{"name": "main_query", "query": {
                "datasetName": "ds_consumption",
                "fields": [
                    {"name": "usage_date", "expression": "`usage_date`"},
                    {"name": "sum(total_dbus)", "expression": "SUM(`total_dbus`)"},
                    {"name": "billing_origin_product", "expression": "`billing_origin_product`"}
                ],
                "disaggregated": False
            }}],
            "spec": {
                "version": 3, "widgetType": "line",
                "encodings": {
                    "x": {"fieldName": "usage_date", "scale": {"type": "temporal"}, "displayName": "Date"},
                    "y": {"fieldName": "sum(total_dbus)", "scale": {"type": "quantitative"}, "displayName": "DBUs"},
                    "color": {"fieldName": "billing_origin_product", "scale": {"type": "categorical"}, "displayName": "Product"}
                },
                "frame": {"showTitle": True, "title": "DBU Consumption Over Time"}
            }
        },
        "position": {"x": 0, "y": 9, "width": 3, "height": 4}
    })

    # Bar: Most active users by query count
    p3_layout.append({
        "widget": {
            "name": gen_id(),
            "queries": [{"name": "main_query", "query": {
                "datasetName": "ds_query_activity",
                "fields": [
                    {"name": "user_name", "expression": "`user_name`"},
                    {"name": "sum(query_count)", "expression": "SUM(`query_count`)"}
                ],
                "disaggregated": False
            }}],
            "spec": {
                "version": 3, "widgetType": "bar",
                "encodings": {
                    "x": {"fieldName": "user_name", "scale": {"type": "categorical", "sort": {"by": "y-reversed"}}, "displayName": "User"},
                    "y": {"fieldName": "sum(query_count)", "scale": {"type": "quantitative"}, "displayName": "Query Count"},
                    "label": {"show": True}
                },
                "frame": {"showTitle": True, "title": "Most Active Users (Query Count)"},
                "mark": {"colors": ["#00A972"]}
            }
        },
        "position": {"x": 3, "y": 9, "width": 3, "height": 4}
    })

    # Line: Query activity over time
    p3_layout.append({
        "widget": {
            "name": gen_id(),
            "queries": [{"name": "main_query", "query": {
                "datasetName": "ds_query_activity",
                "fields": [
                    {"name": "query_date", "expression": "`query_date`"},
                    {"name": "sum(query_count)", "expression": "SUM(`query_count`)"}
                ],
                "disaggregated": False
            }}],
            "spec": {
                "version": 3, "widgetType": "line",
                "encodings": {
                    "x": {"fieldName": "query_date", "scale": {"type": "temporal"}, "displayName": "Date"},
                    "y": {"fieldName": "sum(query_count)", "scale": {"type": "quantitative"}, "displayName": "Queries"}
                },
                "frame": {"showTitle": True, "title": "Query Activity Over Time"}
            }
        },
        "position": {"x": 0, "y": 13, "width": 6, "height": 4}
    })

    pages.append({
        "name": p3_id,
        "displayName": "Lineage & Usage",
        "pageType": "PAGE_TYPE_CANVAS",
        "layout": p3_layout
    })

    return {
        "datasets": datasets,
        "pages": pages,
        "uiSettings": {
            "theme": {"widgetHeaderAlignment": "ALIGNMENT_UNSPECIFIED"},
            "applyModeEnabled": False
        }
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build Audit & Observability Dashboard")
    parser.add_argument("--catalog", default="audit_observability_catalog", help="Catalog name")
    args = parser.parse_args()

    dashboard = build_dashboard(args.catalog)
    print(json.dumps(dashboard, indent=2))
