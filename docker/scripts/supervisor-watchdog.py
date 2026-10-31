#!/usr/bin/env python3
# supervisord event listener: stops supervisord (and therefore the container)
# when a watched program fails, so the orchestrator (Kubernetes) sees the failure,
# counts the restart and keeps the logs available with `kubectl logs --previous`.

import os
import signal
import sys

PROGRAMS = {p.strip() for p in os.environ.get('WATCHDOG_PROGRAMS', 'odoo').split(',') if p.strip()}


def log(message):
    sys.stderr.write('[watchdog] %s\n' % message)
    sys.stderr.flush()


def send(message):
    sys.stdout.write(message)
    sys.stdout.flush()


def parse(line):
    return dict(token.split(':', 1) for token in line.split() if ':' in token)


def is_failure(event, fields):
    if fields.get('processname') not in PROGRAMS:
        return False
    if event == 'PROCESS_STATE_EXITED':
        return fields.get('expected') == '0'
    return event in ('PROCESS_STATE_BACKOFF', 'PROCESS_STATE_FATAL')


def main():
    log('watching %s' % ', '.join(sorted(PROGRAMS)))
    while True:
        send('READY\n')
        header = parse(sys.stdin.readline())
        payload = sys.stdin.read(int(header.get('len', 0)))
        event = header.get('eventname', '')
        fields = parse(payload.split('\n', 1)[0])
        if is_failure(event, fields):
            log('%s entered %s (from %s), stopping supervisord so the container exits'
                % (fields.get('processname'), event.replace('PROCESS_STATE_', ''), fields.get('from_state')))
            os.kill(os.getppid(), signal.SIGTERM)
        send('RESULT 2\nOK')


if __name__ == '__main__':
    main()
