#!/usr/bin/env python3
"""Usage: log-tee.py [--no-file] NAME

Reads lines from stdin and
  - appends them to $LOG_DIR/NAME.log (default ~/logs). The file is rotated when it
    reaches $LOG_MAX_BYTES (default 20M) and gzipped, keeping $LOG_BACKUPS old files (default 5):
    NAME.log.1.gz is the newest, NAME.log.$LOG_BACKUPS.gz the oldest.
  - echoes them to stdout (the container log) when NAME is listed in $LOG_STDOUT_PROGRAMS
    (comma or space separated, 'all' for every program). When more than one program is listed,
    the stdout lines are prefixed with [NAME].

SIGTERM, SIGINT and SIGHUP are ignored: the tee exits when its input is closed, so the last lines
of a stopping program are never lost.
"""

import gzip
import logging
import logging.handlers
import os
import shutil
import signal
import sys

SIZE_UNITS = {'K': 1024, 'M': 1024 ** 2, 'G': 1024 ** 3}


def parse_size(value, default):
    value = (value or '').strip().upper().rstrip('B')
    if not value:
        return default
    try:
        if value[-1] in SIZE_UNITS:
            return int(float(value[:-1]) * SIZE_UNITS[value[-1]])
        return int(value)
    except ValueError:
        return default


def parse_int(value, default):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def stdout_programs():
    raw = os.environ.get('LOG_STDOUT_PROGRAMS', '')
    return [p for p in raw.replace(',', ' ').split() if p]


def gzip_rotator(source, dest):
    with open(source, 'rb') as src, gzip.open(dest, 'wb') as dst:
        shutil.copyfileobj(src, dst)
    os.remove(source)


def file_handler(name):
    log_dir = os.environ.get('LOG_DIR') or os.path.join(os.path.expanduser('~'), 'logs')
    path = os.path.join(log_dir, name + '.log')
    try:
        os.makedirs(log_dir, exist_ok=True)
        handler = logging.handlers.RotatingFileHandler(
            path,
            maxBytes=parse_size(os.environ.get('LOG_MAX_BYTES'), 20 * 1024 ** 2),
            backupCount=parse_int(os.environ.get('LOG_BACKUPS'), 5),
            encoding='utf-8',
        )
    except OSError as e:
        sys.stderr.write('[log-tee] cannot write %s: %s\n' % (path, e))
        return None
    handler.namer = lambda filename: filename + '.gz'
    handler.rotator = gzip_rotator
    handler.setFormatter(logging.Formatter('%(message)s'))
    return handler


def main(argv):
    write_file = True
    if argv and argv[0] == '--no-file':
        write_file = False
        argv = argv[1:]
    if len(argv) != 1:
        sys.stderr.write(__doc__)
        return 2
    name = argv[0]

    for sig in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
        signal.signal(sig, signal.SIG_IGN)
    logging.raiseExceptions = False

    handler = file_handler(name) if write_file else None

    programs = stdout_programs()
    out = None
    prefix = b''
    if 'all' in programs or name in programs:
        out = sys.stdout.buffer
        if len(programs) > 1 or 'all' in programs:
            prefix = ('[%s] ' % name).encode()

    for raw in iter(sys.stdin.buffer.readline, b''):
        if not raw.endswith(b'\n'):
            raw += b'\n'
        if handler:
            line = raw.decode('utf-8', 'replace').rstrip('\r\n')
            handler.handle(logging.makeLogRecord({'msg': line}))
        if out:
            try:
                out.write(prefix + raw)
                out.flush()
            except OSError:
                out = None

    if handler:
        handler.close()
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
