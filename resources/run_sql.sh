#!/bin/bash
# Execute a SQL statement against the audit-obs workspace
# Usage: ./resources/run_sql.sh "SELECT 1"
set -euo pipefail

PROFILE="${PROFILE:-audit-obs}"
WAREHOUSE_ID="${WAREHOUSE_ID:-a32882879825bc8e}"
STATEMENT="$1"

RESULT=$(databricks api post /api/2.0/sql/statements \
  --profile="$PROFILE" \
  --json "{
    \"warehouse_id\": \"$WAREHOUSE_ID\",
    \"statement\": $(python3 -c "import json; print(json.dumps('''$STATEMENT'''))"),
    \"wait_timeout\": \"120s\"
  }" 2>&1)

STATE=$(echo "$RESULT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('status',{}).get('state','UNKNOWN'))" 2>/dev/null || echo "ERROR")
if [ "$STATE" = "SUCCEEDED" ]; then
  echo "OK: $STATE"
  echo "$RESULT" | python3 -c "
import sys,json
d=json.load(sys.stdin)
cols = [c['name'] for c in d.get('manifest',{}).get('schema',{}).get('columns',[])]
rows = d.get('result',{}).get('data_array',[])
if cols: print('\t'.join(cols))
for r in rows[:20]: print('\t'.join(str(v) for v in r))
" 2>/dev/null
else
  echo "FAILED: $STATE"
  echo "$RESULT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('status',{}).get('error',{}).get('message','unknown error'))" 2>/dev/null || echo "$RESULT"
fi
