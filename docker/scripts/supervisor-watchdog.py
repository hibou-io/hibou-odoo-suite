#!/usr/bin/env python3
# supervisord event listener: stops supervisord (and therefore the container)
# when a watched program ends, so the orchestrator (Kubernetes) sees it,
# counts the restart and keeps the logs available with `kubectl logs --previous`.
#
#   WATCHDOG_PROGRAMS   long running programs: an unexpected exit, BACKOFF or FATAL
#                       stops supervisord (default: odoo)
#   WATCHDOG_EXIT_ANY   one-shot programs: any exit, successful or not, stops supervisord
#   WATCHDOG_EXIT_FILE  the exit status of the program is written to this file,
#                       the entrypoint uses it as the container exit code

import os
import signal
import sys


def names(var, default=''):
    return {p for p in os.environ.get(var, default).replace(',', ' ').split() if p}


PROGRAMS = names('WATCHDOG_PROGRAMS', 'odoo')
EXIT_ANY = names('WATCHDOG_EXIT_ANY')
EXIT_FILE = os.environ.get('WATCHDOG_EXIT_FILE', '')


def log(message):
    sys.stderr.write('[watchdog] %s\n' % message)
    sys.stderr.flush()


def send(message):
    sys.stdout.write(message)
    sys.stdout.flush()


def parse(line):
    return dict(token.split(':', 1) for token in line.split() if ':' in token)


def should_stop(event, fields):
    name = fields.get('processname')
    if name not in PROGRAMS and name not in EXIT_ANY:
        return False
    if event == 'PROCESS_STATE_EXITED':
        return name in EXIT_ANY or fields.get('expected') == '0'
    return event in ('PROCESS_STATE_BACKOFF', 'PROCESS_STATE_FATAL')


def exit_status(event, fields):
    status = None
    try:
        from supervisor import childutils
        rpc = childutils.getRPCInterface(os.environ)
        info = rpc.supervisor.getProcessInfo('%s:%s' % (fields.get('groupname'), fields.get('processname')))
        status = int(info.get('exitstatus', 0))
    except Exception as exc:
        log('could not read the exit status of %s (%s)' % (fields.get('processname'), exc))
    success = event == 'PROCESS_STATE_EXITED' and fields.get('expected') == '1'
    if status is None or status < 0 or status > 255:
        return 0 if success else 1
    if status == 0 and not success:
        return 1
    return status


def stop(event, fields):
    status = exit_status(event, fields)
    log('%s entered %s (from %s, exit status %s), stopping supervisord so the container exits'
        % (fields.get('processname'), event.replace('PROCESS_STATE_', ''), fields.get('from_state'), status))
    if EXIT_FILE:
        try:
            with open(EXIT_FILE, 'w') as f:
                f.write('%d\n' % status)
        except OSError as exc:
            log('could not write %s (%s)' % (EXIT_FILE, exc))
    os.kill(os.getppid(), signal.SIGTERM)


def main():
    log('watching %s' % ', '.join(
        ['%s (on failure)' % p for p in sorted(PROGRAMS)] + ['%s (on any exit)' % p for p in sorted(EXIT_ANY)]))
    stopping = False
    while True:
        send('READY\n')
        header = parse(sys.stdin.readline())
        payload = sys.stdin.read(int(header.get('len', 0)))
        event = header.get('eventname', '')
        fields = parse(payload.split('\n', 1)[0])
        if not stopping and should_stop(event, fields):
            stopping = True
            stop(event, fields)
        send('RESULT 2\nOK')


if __name__ == '__main__':
    main()
