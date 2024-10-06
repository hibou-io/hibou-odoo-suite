# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

import psutil
import os
import signal
import sys

# once upon a time
# we tried to find 'odoo' and 'python'
# but sometimes, it would be something like "/usr/local/bin/...."
# so we now just try not to signal/kill 'node'
PID = 1
PNAME = 'node'
KILL_OTHER = sys.argv[1] == 'KILL_OTHER' if len(sys.argv) >= 2 else False
if KILL_OTHER:
    print('Will find other Odoo Processes and Kill them.')

is_foreground = False
foreground_name = ''
for proc in psutil.process_iter():
    try:
        process_name = proc.name()
        process_id = proc.pid
        print('Inspecting %s:%s' % (process_id, process_name))
        if process_id == PID:
            is_foreground = process_name != PNAME
            foreground_name = process_name
            if not KILL_OTHER:
                break
        if process_id != PID and KILL_OTHER and process_name != PNAME:
            print('Killing %s:%s' % (process_id, process_name))
            os.kill(process_id, signal.SIGKILL)
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
        pass

if not is_foreground:
    print('Odoo is not the foreground process.')
    exit(-1)

print('Signalling reload to foreground process "%s"' % (foreground_name, ))
os.kill(PID, signal.SIGHUP)

