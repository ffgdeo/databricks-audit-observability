#!/usr/bin/env python3
import json, subprocess

d = {
    "datasets": [{"name":"test","displayName":"Test","queryLines":["SELECT 1 AS col1, 'hello' AS col2"]}],
    "pages": [{"name":"p1","displayName":"Test","pageType":"PAGE_TYPE_CANVAS","layout":[
        {"widget":{"name":"w1","queries":[{"name":"main_query","query":{"datasetName":"test","fields":[
            {"name":"col1","expression":"`col1`"},{"name":"col2","expression":"`col2`"}
        ],"disaggregated":True}}],
        "spec":{"version":1,"widgetType":"table","encodings":{"columns":[
            {"fieldName":"col1","title":"Col1"},
            {"fieldName":"col2","title":"Col2"}
        ]},"frame":{"showTitle":True,"title":"Minimal (no displayAs)"}}},
        "position":{"x":0,"y":0,"width":6,"height":4}},

        {"widget":{"name":"w2","queries":[{"name":"main_query","query":{"datasetName":"test","fields":[
            {"name":"col1","expression":"`col1`"},{"name":"col2","expression":"`col2`"}
        ],"disaggregated":True}}],
        "spec":{"version":1,"widgetType":"table","encodings":{"columns":[
            {"fieldName":"col1","displayAs":"string","title":"Col1"},
            {"fieldName":"col2","displayAs":"string","title":"Col2"}
        ]},"frame":{"showTitle":True,"title":"With displayAs"}}},
        "position":{"x":0,"y":4,"width":6,"height":4}},

        {"widget":{"name":"w3","queries":[{"name":"main_query","query":{"datasetName":"test","fields":[
            {"name":"col1","expression":"`col1`"},{"name":"col2","expression":"`col2`"}
        ],"disaggregated":True}}],
        "spec":{"version":2,"widgetType":"table","encodings":{"columns":[
            {"fieldName":"col1","title":"Col1"},
            {"fieldName":"col2","title":"Col2"}
        ]},"frame":{"showTitle":True,"title":"Version 2 (no displayAs)"}}},
        "position":{"x":0,"y":8,"width":6,"height":4}}
    ]}]
}

payload = json.dumps({"serialized_dashboard": json.dumps(d)})
r = subprocess.run(["databricks", "api", "patch", "/api/2.0/lakeview/dashboards/01f11bca11f4192f9280a956dcb895b6",
                     "--profile=audit-obs", "--json", payload], capture_output=True, text=True)
print(r.stdout[:200])
