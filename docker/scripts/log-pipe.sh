#!/bin/bash
# Usage: log-pipe.sh [--no-file] NAME COMMAND [ARGS...]
# Execs COMMAND with stdout and stderr merged into log-tee.py, which writes a rotating
# gzipped $LOG_DIR/NAME.log and echoes to the container stdout if NAME is in $LOG_STDOUT_PROGRAMS.
# COMMAND keeps this PID, so supervisord signals and exit codes reach it directly.

TEE_ARGS=()
if [[ "$1" == "--no-file" ]]; then
    TEE_ARGS+=("$1")
    shift
fi
name="$1"
shift

exec > >(exec python3 "$(dirname "$0")/log-tee.py" "${TEE_ARGS[@]}" "$name") 2>&1
exec "$@"
