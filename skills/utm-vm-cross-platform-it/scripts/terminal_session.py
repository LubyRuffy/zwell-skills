#!/usr/bin/env python3
"""One owned macOS Terminal tab, bounded job, detached cleanup, fail-stop gate.
Run inside a NEW dedicated guest Terminal tab; never in an existing/manual tab.
"""
import argparse
import errno
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
import uuid


def write(path, value):
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
    temp.replace(path)


def terminal(tty, close=False, token="", claim=False):
    # Match the claimed token AND tty, never a stale tab index or front window.
    # Raw codes are from Terminal.sdef; they avoid compile-time dictionary lookup
    # but still use ordinary AppleEvents and require the same OS permission.
    script = '''on run argv
set targetTTY to item 1 of argv
set matches to 0
tell application "Terminal"
repeat with w in every «class cwin»
repeat with t in every «class ttab» of w
if «property ttty» of t is targetTTY and ((item 4 of argv is "claim") or («property titl» of t is item 3 of argv)) then
set matches to matches + 1
end if
end repeat
end repeat
if matches is 0 then return "absent"
if matches is not 1 then return "ambiguous"
repeat with w in every «class cwin»
repeat with t in every «class ttab» of w
if «property ttty» of t is targetTTY and ((item 4 of argv is "claim") or («property titl» of t is item 3 of argv)) then
if item 4 of argv is "claim" then set «property titl» of t to item 3 of argv
if item 2 of argv is "close" then
if «property busy» of t then return "busy"
«event coreclos» t
return "closed"
else
return "present"
end if
end if
end repeat
end repeat
end tell
end run'''
    p = subprocess.run(['osascript', '-e', script, tty, 'close' if close else 'inspect', token, 'claim' if claim else 'check'],
                       capture_output=True, text=True, timeout=5)
    if p.returncode:
        raise RuntimeError('Terminal automation failed: ' + p.stderr.strip())
    return p.stdout.strip()


def tty_holders(tty):
    if not Path(tty).exists():
        return []
    p = subprocess.run(['/usr/sbin/lsof', '-n', '-t', tty],
                       capture_output=True, text=True, timeout=5)
    if p.returncode not in (0, 1) or (p.returncode == 1 and p.stderr.strip()):
        raise RuntimeError('cannot verify tty holders: ' + p.stderr.strip())
    return p.stdout.split()


def group_alive(pgid):
    try:
        os.killpg(pgid, 0)
        return True
    except ProcessLookupError:
        return False


def require_waitid():
    """Check the guardian's exact non-reaping wait without creating a child."""
    waitid = getattr(os, 'waitid', None)
    names = ('P_PID', 'WEXITED', 'WNOHANG', 'WNOWAIT', 'CLD_EXITED')
    constants = [getattr(os, name, None) for name in names]
    missing = [name for name, value in zip(names, constants) if not isinstance(value, int)]
    if not callable(waitid):
        missing.insert(0, 'waitid')
    message = f'{sys.executable}: requires working os.waitid with WNOWAIT (CPython macOS 3.13+)'
    if missing:
        raise RuntimeError(f'{message}; missing: {", ".join(missing)}')
    pid_type, exited, nohang, nowait, normal_exit = constants
    flags = exited | nohang | nowait
    try:
        # Our PID cannot name one of our children; ECHILD is the safe result.
        waitid(pid_type, os.getpid(), flags)
    except OSError as exc:
        if exc.errno == errno.ECHILD:
            return waitid, pid_type, flags, normal_exit
        raise RuntimeError(f'{message}; probe failed: {exc}') from exc
    except NotImplementedError as exc:
        raise RuntimeError(f'{message}; probe not implemented: {exc}') from exc
    raise RuntimeError(f'{message}; probe did not report ECHILD')


def stop_group(child):
    # Child remains unreaped until signals are sent: its PID cannot be reused.
    if group_alive(child.pid):
        os.killpg(child.pid, signal.SIGTERM)
        time.sleep(.2)
        if group_alive(child.pid):
            os.killpg(child.pid, signal.SIGKILL)
    child.wait(timeout=5)
    return not group_alive(child.pid)


def clean_tab(tty, inspect=terminal, holders=tty_holders, sleep=time.sleep):
    for _ in range(20):
        state = inspect(tty, True)
        if state in ('closed', 'absent'):
            # Tab absence alone is not enough: also check holders of this TTY.
            if not holders(tty):
                return True
        elif state != 'busy':
            return False
        sleep(.25)
    return False


def guard(root, gate, tty, timeout, command, token=""):
    result = {'tty': tty, 'cleanup_complete': False, 'command_exit': None}
    child = None
    clean_process = False
    try:
        waitid, pid_type, wait_flags, normal_exit = require_waitid()
        with (root / 'stdout').open('wb') as out, (root / 'stderr').open('wb') as err:
            child = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=out,
                                     stderr=err, start_new_session=True)
            write(root / 'running.json', {'pid': child.pid, 'pgid': child.pid, 'tty': tty})
            deadline = time.monotonic() + timeout
            # waitid WNOWAIT keeps the process identity reserved while we kill descendants.
            while True:
                ended = waitid(pid_type, child.pid, wait_flags)
                if ended:
                    result['command_exit'] = ended.si_status if ended.si_code == normal_exit else -ended.si_status
                    result['reason'] = 'exited'
                    break
                if (root / 'cancel').exists() or time.monotonic() >= deadline:
                    result['reason'] = 'cancelled' if (root / 'cancel').exists() else 'timeout'
                    break
                time.sleep(.1)
            clean_process = stop_group(child)
    except BaseException as exc:
        result['error'] = str(exc)
        if child is not None:
            try:
                clean_process = stop_group(child)
            except Exception as cleanup_exc:
                result['process_cleanup_error'] = str(cleanup_exc)
        else:
            clean_process = True
    finally:
        result['process_cleanup_complete'] = clean_process
        try:
            # run parent and .command shell must finish before a tab is no longer busy.
            result['terminal_cleanup_complete'] = clean_tab(tty, inspect=lambda t, close: terminal(t, close, token))
        except Exception as exc:
            result['terminal_cleanup_complete'] = False
            result['terminal_cleanup_error'] = str(exc)
        result['cleanup_complete'] = clean_process and result['terminal_cleanup_complete']
        write(root / 'result.json', result)
        if result['cleanup_complete']:
            (gate / 'owner.json').unlink()
            gate.rmdir()
    return 0 if result.get('command_exit') == 0 and result['cleanup_complete'] else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['status', 'run', '_guard', 'cancel'])
    parser.add_argument('--state', type=Path, required=True, help='same private guest state root for every launcher')
    parser.add_argument('--evidence', type=Path)
    parser.add_argument('--timeout', type=float, default=60)
    parser.add_argument('--tty')
    parser.add_argument('--token', default='')

    a, command = parser.parse_known_args()
    a.state = a.state.expanduser().resolve()
    gate = a.state / 'active'
    if a.action == 'status':
        if gate.exists():
            print('blocked')
            return 1
        try:
            require_waitid()
        except RuntimeError as exc:
            print('blocked')
            print(exc, file=sys.stderr)
            return 1
        print('ready')
        return 0
    if a.action == 'cancel':
        owner = json.loads((gate / 'owner.json').read_text())
        Path(owner['evidence'], 'cancel').touch(exist_ok=True)
        return 0
    command = command[1:] if command[:1] == ['--'] else command
    if a.action == '_guard':
        return guard(a.evidence, gate, a.tty, a.timeout, command, a.token)
    if sys.platform != 'darwin' or not command or not (0 < a.timeout <= 3600):
        parser.error('run requires macOS, a command, and timeout in (0, 3600]')
    if a.evidence is None:
        parser.error('--evidence is required')
    try:
        require_waitid()
    except RuntimeError as exc:
        parser.error(str(exc))
    tty = os.ttyname(0)
    token = 'utm-owned-' + uuid.uuid4().hex
    if terminal(tty, token=token, claim=True) != 'present':
        raise RuntimeError('cannot uniquely bind this dedicated Terminal tab')
    a.state.mkdir(parents=True, exist_ok=True, mode=0o700)
    gate.mkdir(mode=0o700)  # Atomic fail-stop admission. Never auto-remove stale/failed gates.
    root = a.evidence.expanduser().resolve()
    try:
        root.mkdir(parents=True, mode=0o700)  # refuse reused evidence
        write(gate / 'owner.json', {'evidence': str(root), 'tty': tty, 'token': token})
        with (root / 'guardian.log').open('wb') as log:
            p = subprocess.Popen([sys.executable, str(Path(__file__).resolve()), '_guard',
                                  '--state', str(a.state), '--evidence', str(root),
                                  '--tty', tty, '--token', token, '--timeout', str(a.timeout), '--', *command],
                                 stdin=subprocess.DEVNULL, stdout=log, stderr=log,
                                 start_new_session=True)
        print(json.dumps({'guardian_pid': p.pid, 'evidence': str(root)}))
        return 0  # The .command must now exit, not exec an interactive shell.
    except BaseException:
        # Preserve gate for an uncertain spawn; never allow another terminal storm.
        raise


if __name__ == '__main__':
    raise SystemExit(main())
