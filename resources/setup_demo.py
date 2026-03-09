#!/usr/bin/env python3
"""
Setup the audit & observability demo by executing SQL statements.
Usage: python3 resources/setup_demo.py --profile audit-obs --warehouse a32882879825bc8e [--catalog audit_observability_catalog]
"""

import subprocess
import json
import sys
import argparse
import time


def run_sql(statement: str, profile: str, warehouse_id: str) -> dict:
    """Execute a SQL statement via Databricks API."""
    payload = json.dumps({
        "warehouse_id": warehouse_id,
        "statement": statement,
        "wait_timeout": "50s"
    })
    result = subprocess.run(
        ["databricks", "api", "post", "/api/2.0/sql/statements",
         f"--profile={profile}", "--json", payload],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        return {"status": {"state": "ERROR"}, "error": result.stderr}
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return {"status": {"state": "ERROR"}, "error": result.stdout}


def get_state(result: dict) -> str:
    return result.get("status", {}).get("state", "UNKNOWN")


def get_error(result: dict) -> str:
    return result.get("status", {}).get("error", {}).get("message", str(result.get("error", "unknown")))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", default="audit-obs")
    parser.add_argument("--warehouse", default="a32882879825bc8e")
    parser.add_argument("--catalog", default="audit_observability_catalog")
    args = parser.parse_args()

    catalog = args.catalog

    # Split SQL files into individual statements
    sql_files = [
        "src/sql/01_create_schemas_and_tables.sql",
        "src/sql/02_create_grants.sql",
        "src/sql/03_generate_lineage.sql",
    ]

    for sql_file in sql_files:
        print(f"\n{'='*60}")
        print(f"Executing: {sql_file}")
        print(f"{'='*60}")

        with open(sql_file, 'r') as f:
            content = f.read()

        # Replace variable references
        content = content.replace("${var.catalog}", catalog)

        # Split into individual statements (skip comments and empty lines)
        statements = []
        current = []
        for line in content.split('\n'):
            stripped = line.strip()
            if stripped.startswith('--') or not stripped:
                continue
            current.append(line)
            if stripped.endswith(';'):
                stmt = '\n'.join(current).strip().rstrip(';')
                if stmt:
                    statements.append(stmt)
                current = []

        for i, stmt in enumerate(statements):
            short = stmt[:80].replace('\n', ' ')
            print(f"\n  [{i+1}/{len(statements)}] {short}...")
            result = run_sql(stmt, args.profile, args.warehouse)
            state = get_state(result)
            if state == "SUCCEEDED":
                print(f"  -> OK")
            else:
                error = get_error(result)
                print(f"  -> {state}: {error}")
                # Continue on grant errors (groups may not exist)
                if "GRANT" in stmt.upper() and "does not exist" in error.lower():
                    print(f"  -> (skipping - group doesn't exist yet)")

    print(f"\n{'='*60}")
    print("Setup complete!")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
