import psutil
import os
import signal

PID = 1 
PNAME = 'odoo'
is_foreground = False
for proc in psutil.process_iter():
    try:
        process_name = proc.name()
        process_id = proc.pid
        if process_id == PID:
            is_foreground = process_name == PNAME
            break
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
        pass

if not is_foreground:
    print('Odoo is not the foreground process.')
    exit(-1)

print('Signalling reload to Odoo')
os.kill(PID, signal.SIGHUP)

