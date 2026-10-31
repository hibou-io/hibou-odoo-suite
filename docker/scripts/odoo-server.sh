#!/bin/bash
set -eo pipefail

source /opt/odoo-scripts/odoo-env.sh

ODOO_ARGS=()
if [[ -s "$ODOO_ARGS_FILE" ]]; then
    mapfile -d '' -t ODOO_ARGS < "$ODOO_ARGS_FILE"
fi

wait-for-psql.py "${DB_ARGS[@]}" --timeout="${ODOO_DB_WAIT_TIMEOUT:-30}"
exec odoo "${ODOO_ARGS[@]}" "${DB_ARGS[@]}"
