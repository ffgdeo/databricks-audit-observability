#!/bin/bash
# Enable system schemas required for the audit & observability dashboard
# Usage: ./resources/enable_system_schemas.sh [--profile PROFILE]

set -euo pipefail

PROFILE="${1:---profile DEFAULT}"

echo "Fetching metastore ID..."
METASTORE_ID=$(databricks unity-catalog metastores list $PROFILE 2>/dev/null | jq -r '.[0].metastore_id // empty')

if [ -z "$METASTORE_ID" ]; then
  # Try current metastore assignment
  METASTORE_ID=$(databricks unity-catalog current-metastore-assignment get $PROFILE 2>/dev/null | jq -r '.metastore_id // empty')
fi

if [ -z "$METASTORE_ID" ]; then
  echo "ERROR: Could not determine metastore ID. Ensure you are authenticated."
  exit 1
fi

echo "Metastore ID: $METASTORE_ID"

for schema in access billing query; do
  echo "Enabling system schema: $schema..."
  databricks api put "/api/2.0/unity-catalog/metastores/$METASTORE_ID/systemschemas/$schema" $PROFILE 2>/dev/null || echo "  (may already be enabled)"
done

echo "Done. System schemas enabled."
