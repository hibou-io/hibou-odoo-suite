#!/usr/bin/env python3
# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

import argparse
import os
import signal
import subprocess
import sys
import time

import psutil

COMMAND = 'odoo-reload'
PROGRAM = os.environ.get('ODOO_SUPERVISOR_PROGRAM', 'odoo')
ODOO_NAMES = {'odoo', 'odoo-bin', 'odoo-run.py'}
LEGACY_ARGS = {'KILL_OTHER': '--kill-others'}

DESCRIPTION = """\
Reload the Odoo server managed by supervisord (program '%(program)s').

By default this sends SIGHUP to the supervised Odoo, which makes it reload in place
(re-reading code and configuration). If the program is stopped it is started instead.

Odoo processes started from Athene/Theia terminals or debug sessions are NOT touched
unless you pass --kill-others. They keep running (holding ports such as 8069/8072)
even after the IDE lost their terminal.""" % {'program': PROGRAM}

EPILOG = """\
examples:
  %(cmd)s                          reload the supervised Odoo (SIGHUP)
  %(cmd)s --list                   list the supervised and the 'other' Odoo processes
  %(cmd)s --kill-others            kill the 'other' Odoo processes, then reload
  %(cmd)s --kill-others --no-reload
                                    only kill the 'other' Odoo processes
  %(cmd)s --kill-others --restart  kill the 'other' Odoo processes, then fully restart

'other' Odoo processes are all odoo / odoo-bin / odoo-run.py processes that are neither the
supervised '%(program)s' program (nor its workers) nor a parent of this command.
Processes marked 'orphaned' lost their terminal and were re-parented to PID 1.

related supervisorctl commands:
  supervisorctl status
  supervisorctl signal QUIT %(program)s     dump Odoo stack traces to the container log
  supervisorctl stop %(program)s            free the ports to run Odoo from the IDE debugger
""" % {'cmd': COMMAND, 'program': PROGRAM}


def parse_args(argv):
    parser = argparse.ArgumentParser(
        prog=COMMAND,
        description=DESCRIPTION,
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument('-k', '--kill-others', action='store_true',
                        help="kill all 'other' Odoo processes (e.g. left behind by IDE terminals) "
                             "before reloading. Legacy spelling: KILL_OTHER")
    parser.add_argument('-l', '--list', action='store_true',
                        help='only list Odoo processes, do not kill or reload anything')
    parser.add_argument('-r', '--restart', action='store_true',
                        help="stop and start the supervised Odoo instead of reloading it with SIGHUP")
    parser.add_argument('-n', '--no-reload', action='store_true',
                        help='do not reload/restart the supervised Odoo (use with --kill-others)')
    parser.add_argument('-t', '--timeout', type=float, default=10.0,
                        help='seconds to wait after SIGTERM before sending SIGKILL (default: %(default)s)')
    return parser.parse_args([LEGACY_ARGS.get(a, a) for a in argv])


def supervisorctl(*args):
    try:
        result = subprocess.run(['supervisorctl', *args], capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.SubprocessError) as e:
        return None, str(e)
    return result.returncode, (result.stdout + result.stderr).strip()


def supervised_pid():
    # None: supervisord unavailable, 0: program not running, >0: program pid
    _code, output = supervisorctl('pid', PROGRAM)
    if not output or not output.isdigit():
        return None
    return int(output)


def is_odoo_process(proc):
    try:
        cmdline = proc.cmdline()
    except psutil.Error:
        return False
    if not cmdline:
        return False
    if os.path.basename(cmdline[0]) in ODOO_NAMES:
        return True
    if not os.path.basename(cmdline[0]).startswith('python'):
        return False
    parts = iter(cmdline[1:])
    for part in parts:
        if part == '-m':
            return next(parts, '').split('.')[0] == 'odoo'
        if part.startswith('-'):
            continue
        return os.path.basename(part) in ODOO_NAMES
    return False


def foreground_odoo_pid():
    try:
        return 1 if is_odoo_process(psutil.Process(1)) else 0
    except psutil.Error:
        return 0


def protected_pids(root_pid):
    pids = {os.getpid()}
    try:
        pids.update(p.pid for p in psutil.Process().parents())
    except psutil.Error:
        pass
    if root_pid:
        pids.add(root_pid)
        try:
            pids.update(c.pid for c in psutil.Process(root_pid).children(recursive=False))
        except psutil.Error:
            pass
    return pids


def odoo_processes():
    procs = []
    for proc in psutil.process_iter():
        if proc.pid != os.getpid() and is_odoo_process(proc):
            procs.append(proc)
    return sorted(procs, key=lambda p: p.pid)


def describe(proc):
    try:
        with proc.oneshot():
            ppid = proc.ppid()
            age = int(time.time() - proc.create_time())
            user = proc.username()
            cmdline = ' '.join(proc.cmdline())
    except psutil.Error:
        return '  %7s  (gone)' % proc.pid
    if len(cmdline) > 140:
        cmdline = cmdline[:137] + '...'
    hours, rest = divmod(age, 3600)
    minutes, seconds = divmod(rest, 60)
    orphaned = '  [orphaned]' if ppid == 1 else ''
    return '  %7s  ppid=%-7s %-8s %3d:%02d:%02d  %s%s' % (
        proc.pid, ppid, user, hours, minutes, seconds, cmdline, orphaned)


def print_processes(title, procs):
    print('%s (%d):' % (title, len(procs)))
    if not procs:
        print('  none')
    for proc in procs:
        print(describe(proc))


def warn_others(others):
    print()
    print("WARNING: %d other Odoo process(es) are running and were NOT killed:" % len(others))
    for proc in others:
        print(describe(proc))
    print('They may hold the Odoo ports (8069/8072) or keep old code running.')
    print('To kill them and reload:      %s --kill-others' % COMMAND)
    print('To only kill them:            %s --kill-others --no-reload' % COMMAND)
    print('To see all Odoo processes:    %s --list' % COMMAND)
    print()


def kill_others(others, timeout):
    print('Killing %d other Odoo process(es):' % len(others))
    for proc in others:
        print(describe(proc))
    denied = []
    alive = []
    for proc in others:
        try:
            proc.terminate()
            alive.append(proc)
        except psutil.NoSuchProcess:
            pass
        except psutil.AccessDenied:
            denied.append(proc)
    _gone, alive = psutil.wait_procs(alive, timeout=timeout)
    for proc in alive:
        try:
            print('  %s did not stop after %ss, sending SIGKILL' % (proc.pid, timeout))
            proc.kill()
        except psutil.NoSuchProcess:
            pass
        except psutil.AccessDenied:
            denied.append(proc)
    psutil.wait_procs(alive, timeout=5)
    if denied:
        print('ERROR: permission denied for pid(s) %s (owned by another user).'
              % ', '.join(str(p.pid) for p in denied))
        print('Run as root from the host, e.g.: docker exec -u root <container> %s --kill-others'
              % COMMAND)
        return False
    print('Done.')
    return True


def reload_supervised(pid, restart):
    if restart or pid == 0:
        action = 'restart' if pid else 'start'
        print('%sing supervised program "%s"' % (action.capitalize(), PROGRAM))
        code, output = supervisorctl(action, PROGRAM)
        if output:
            print(output)
        if code != 0:
            print('Check the log with: supervisorctl tail %s' % PROGRAM)
        return code == 0
    print('Signalling reload (SIGHUP) to supervised program "%s" (pid %s)' % (PROGRAM, pid))
    os.kill(pid, signal.SIGHUP)
    return True


def reload_legacy(restart):
    if not foreground_odoo_pid():
        print('supervisord is not reachable and Odoo is not the foreground process (PID 1).')
        print('Nothing to reload. Is supervisord running? Try: supervisorctl status')
        return False
    if restart:
        print('--restart is not supported without supervisord, reloading instead.')
    print('Signalling reload (SIGHUP) to foreground Odoo (PID 1)')
    os.kill(1, signal.SIGHUP)
    return True


def main(argv):
    args = parse_args(argv)

    pid = supervised_pid()
    if pid is None:
        print('Note: supervisord is not reachable (`supervisorctl pid %s` failed), '
              'treating PID 1 as the Odoo server.' % PROGRAM)
        root_pid = foreground_odoo_pid()
    else:
        root_pid = pid

    protected = protected_pids(root_pid)
    procs = odoo_processes()
    supervised = [p for p in procs if p.pid in protected]
    others = [p for p in procs if p.pid not in protected]

    if args.list:
        print_processes('Supervised Odoo processes', supervised)
        print_processes('Other Odoo processes', others)
        if others:
            print('Kill the other processes with: %s --kill-others [--no-reload]' % COMMAND)
        return 0

    ok = True
    if args.kill_others:
        if others:
            ok = kill_others(others, args.timeout)
        else:
            print('No other Odoo processes found.')
    elif others:
        warn_others(others)

    if args.no_reload:
        return 0 if ok else 1

    if pid is None:
        ok = reload_legacy(args.restart) and ok
    else:
        ok = reload_supervised(pid, args.restart) and ok
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
