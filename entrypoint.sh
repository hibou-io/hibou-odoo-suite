#!/bin/bash

set -e

# set the postgres database host, port, user and password according to the environment
# and pass them as arguments to the odoo process if not present in the config file
: ${HOST:=${DB_PORT_5432_TCP_ADDR:='db'}}
: ${PORT:=${DB_PORT_5432_TCP_PORT:=5432}}
: ${USER:=${DB_ENV_POSTGRES_USER:=${POSTGRES_USER:='odoo'}}}
: ${PASSWORD:=${DB_ENV_POSTGRES_PASSWORD:=${POSTGRES_PASSWORD:='odoo'}}}

DB_ARGS=()
function check_config() {
    param="$1"
    value="$2"
    if grep -q -E "^\s*\b${param}\b\s*=" "$ODOO_RC" ; then
        value=$(grep -E "^\s*\b${param}\b\s*=" "$ODOO_RC" |cut -d " " -f3|sed 's/["\n\r]//g')
    fi;
    DB_ARGS+=("--${param}")
    DB_ARGS+=("${value}")
}
check_config "db_host" "$HOST"
check_config "db_port" "$PORT"
check_config "db_user" "$USER"
check_config "db_password" "$PASSWORD"

case "$1" in
    flow)
        shift
        wait-for-psql.py ${DB_ARGS[@]} --timeout=60
        : ${DB_NAME:='odoo'}
        : ${DATA_DIR:='/var/lib/odoo'}
        check_config "db_name" "$DB_NAME"
        check_config "data_dir" "$DATA_DIR"
        cd /flow
        FLOW_ARGS=()
        CONTINUE="1"
        while [[ "$#" && $CONTINUE ]]; do
            # We want the -- shifted, but not in the FLOW_ARGS
            if [[ "$1" == "--" ]]; then
                CONTINUE=""
                shift
            fi
            if [[ "$1" && $CONTINUE ]]; then
                FLOW_ARGS+=("$1")
                shift
            else
                # if we shift too many times we exit...
                CONTINUE=""
            fi
        done
        /flow/entrypoint.sh ${FLOW_ARGS[@]} ${DB_ARGS[@]}
        exec /entrypoint.sh "$@"
        ;;
    -- | odoo)
        shift
        if [[ "$1" == "scaffold" ]] ; then
            exec odoo "$@"
        else
            wait-for-psql.py ${DB_ARGS[@]} --timeout=30
            exec odoo "$@" "${DB_ARGS[@]}"
        fi
        ;;
    -*)
        wait-for-psql.py ${DB_ARGS[@]} --timeout=30
        exec odoo "$@" "${DB_ARGS[@]}"
        ;;
    *)
        exec "$@"
esac

exit 1