#!/bin/bash

set -eo pipefail

#    Long running services are managed by supervisord (PID 1):
#      odoo    Odoo server, started with the arguments of the container command
#      athene  Athene/Theia IDE (professional+ images only)
#
#    DEV_MODE=exclusive
#      Only Athene is started. Odoo can be started from a terminal, the IDE,
#      or with `supervisorctl start odoo` (uses the container command arguments).
#    DEV_MODE=1
#      Athene and Odoo are both started. From an Athene terminal:
#        `odoo-reload`                      reload Odoo in place, warns about other Odoo processes
#        `odoo-reload --kill-others`        also kill Odoo processes left behind by IDE terminals
#        `odoo-reload --help`               all options
#        `supervisorctl status`             show the state of all programs
#        `supervisorctl restart odoo`       stop and start Odoo
#        `supervisorctl signal QUIT odoo`   dump stacktraces to the Odoo log (container stdout)
#        `supervisorctl stop odoo`          free the port to run Odoo from the IDE debugger
#      Odoo is restarted by supervisord if it dies, the container keeps running.
#    DEV_MODE=
#      Unset to not use Athene at all.
#
#    DEV_MODE_PATH=/opt/odoo/addons
#      To change the path to start Athene in, useful to get git working.
#
#    DISABLE_ODOO=1
#      Do not autostart the Odoo program (it can still be started with supervisorctl).
#
#    ODOO_DB_WAIT_TIMEOUT=30
#      Seconds the supervised Odoo waits for PostgreSQL before failing (and being retried).
#
#    One-shot Odoo commands (sub-commands such as `shell` or `scaffold`, `--stop-after-init`,
#    `--help`, `--version`), `flow` jobs and arbitrary commands run in the foreground
#    without supervisord.

DEV_MODE="${DEV_MODE:-}"
DISABLE_ODOO="${DISABLE_ODOO:-0}"
ATHENE_ENTRYPOINT="/opt/athene/entrypoint.sh"
SUPERVISOR_CONF="/etc/supervisor/supervisord.conf"
OVERRIDE_DIR="/etc/supervisor/override.d"
ODOO_SCRIPTS_DIR="/opt/odoo-scripts"

# ===========================================================
# Phase 1 — Prepare the development environment
# ===========================================================
if [ "${DEV_MODE_PATH:-}" != "" ] && [ -z "$(ls -A "$DEV_MODE_PATH/.theia" 2>/dev/null)" ]
then
   cp -R /opt/odoo/hibou-suite/.theia "$DEV_MODE_PATH" || true
fi
if [ "${DEV_MODE_PATH:-}" != "" ] && [ -z "$(ls -A "$DEV_MODE_PATH/.pylintrc" 2>/dev/null)" ]
then
   cp -R /opt/odoo/hibou-suite/.pylintrc "$DEV_MODE_PATH" || true
fi

if [ "${DEV_MODE_PATH:-}" == "" ]
then
   export DEV_MODE_PATH=/opt/odoo/hibou-suite
fi
# Patch Theia user settings with MCP defaults (professional+ images only)
if [[ -x "/opt/odoo-tools/init-theia-settings.py" ]]
then
    python3 /opt/odoo-tools/init-theia-settings.py || \
        echo "WARNING: init-theia-settings.py failed (exit $?), continuing anyway" >&2
fi

# ===========================================================
# Phase 2 — Database connection arguments
# ===========================================================
source "$ODOO_SCRIPTS_DIR/odoo-env.sh"

function is_one_shot() {
    if [[ $# -gt 0 && "$1" != -* && "$1" != "server" ]]; then
        return 0
    fi
    local arg
    for arg in "$@"; do
        case "$arg" in
            --stop-after-init|-h|--help|--version)
                return 0
                ;;
        esac
    done
    return 1
}

function run_one_shot() {
    if [[ "${1:-}" == "scaffold" ]]; then
        exec odoo "$@"
    fi
    wait-for-psql.py "${DB_ARGS[@]}" --timeout=30
    exec odoo "$@" "${DB_ARGS[@]}"
}

function start_services() {
    local enable_odoo=0
    local enable_athene=0

    if [[ "$DEV_MODE" == "exclusive" ]]; then
        enable_athene=1
    else
        if [[ "$DISABLE_ODOO" != "1" ]]; then
            enable_odoo=1
        fi
        if [[ -n "$DEV_MODE" ]]; then
            enable_athene=1
        fi
    fi

    if [[ "$enable_athene" == "1" && ! -x "$ATHENE_ENTRYPOINT" ]]; then
        echo "WARNING: DEV_MODE is set but $ATHENE_ENTRYPOINT is not available, Athene will not be started" >&2
        enable_athene=0
    fi

    echo "==> Service configuration:"
    echo "    odoo   : $([ "$enable_odoo" = "1" ] && echo ENABLED || echo DISABLED)"
    echo "    athene : $([ "$enable_athene" = "1" ] && echo ENABLED || echo DISABLED)"

    : > "$ODOO_ARGS_FILE"
    if [[ $# -gt 0 ]]; then
        printf '%s\0' "$@" > "$ODOO_ARGS_FILE"
    fi

    rm -rf "${OVERRIDE_DIR:?}"/*
    mkdir -p "$OVERRIDE_DIR"

    if [[ "$enable_odoo" == "1" ]]; then
        cat > "$OVERRIDE_DIR/odoo.ini" <<EOF
[program:odoo]
autostart=true
EOF
    fi

    if [[ "$enable_athene" == "1" ]]; then
        cat > "$OVERRIDE_DIR/athene.ini" <<EOF
[program:athene]
autostart=true
EOF
    fi

    echo "==> Starting supervisord..."
    exec /usr/bin/supervisord -n -c "$SUPERVISOR_CONF"
}

function dispatch_odoo() {
    if [[ "$DEV_MODE" != "exclusive" ]] && is_one_shot "$@"; then
        run_one_shot "$@"
    fi
    start_services "$@"
}

# ===========================================================
# Phase 3 — Dispatch the container command
# ===========================================================
case "${1:-}" in
    flow)
        shift
        wait-for-psql.py "${DB_ARGS[@]}" --timeout=60
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
            if [[ "${1:-}" && $CONTINUE ]]; then
                FLOW_ARGS+=("$1")
                shift
            else
                # if we shift too many times we exit...
                CONTINUE=""
            fi
        done
        FLOW_STATUS=0
        /flow/entrypoint.sh "${FLOW_ARGS[@]}" "${DB_ARGS[@]}" || FLOW_STATUS=$?
        if [[ $FLOW_STATUS -ne 0 ]]; then
            if [[ "$DEV_MODE" == "exclusive" ]]; then
                echo "WARNING: flow failed (exit $FLOW_STATUS), continuing because DEV_MODE=exclusive" >&2
            else
                exit $FLOW_STATUS
            fi
        fi
        exec /entrypoint.sh "$@"
        ;;
    -- | odoo)
        shift
        dispatch_odoo "$@"
        ;;
    -*)
        dispatch_odoo "$@"
        ;;
    *)
        exec "$@"
esac

# notably do not exit 1 as we can complete a job like a backup
