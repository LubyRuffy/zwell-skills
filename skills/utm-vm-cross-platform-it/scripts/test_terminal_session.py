import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import terminal_session as m


class TerminalLifecycle(unittest.TestCase):
    def test_requires_release_not_only_closed_window(self):
        self.assertFalse(m.clean_tab('/dev/ttys001', lambda *x: 'closed', lambda x: ['17'], lambda _: None))

    def test_busy_or_ambiguous_never_closed(self):
        for state in ('busy', 'ambiguous'):
            self.assertFalse(m.clean_tab('t', lambda *x: state, lambda x: [], lambda _: None))

    def test_released(self):
        self.assertTrue(m.clean_tab('t', lambda *x: 'closed', lambda x: [], lambda _: None))

    def run_guard(self, command, cancel=False, cleanup=True, timeout=2):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d) / 'evidence'; root.mkdir()
            gate = Path(d) / 'active'; gate.mkdir()
            (gate / 'owner.json').write_text('{}')
            if cancel: (root / 'cancel').touch()
            with patch.object(m, 'clean_tab', return_value=cleanup):
                code = m.guard(root, gate, '/dev/test-owned', timeout, command)
            return code, json.loads((root / 'result.json').read_text()), gate.exists()

    def test_success_and_error_both_cleanup(self):
        for status in (0, 7):
            code, r, blocked = self.run_guard([sys.executable, '-c', f'raise SystemExit({status})'])
            self.assertEqual(r['command_exit'], status)
            self.assertTrue(r['cleanup_complete'])
            self.assertFalse(blocked)
            self.assertEqual(code, int(status != 0))

    def test_cancel_timeout_cleanup(self):
        for cancel in (True, False):
            code, r, blocked = self.run_guard([sys.executable, '-c', 'import time; time.sleep(30)'], cancel=cancel, timeout=.2)
            self.assertEqual(r['reason'], 'cancelled' if cancel else 'timeout')
            self.assertTrue(r['cleanup_complete'])
            self.assertFalse(blocked)
            self.assertEqual(code, 1)

    def test_spawn_error_closes_tab(self):
        code, r, blocked = self.run_guard(['/missing/command'])
        self.assertTrue(r['cleanup_complete'])
        self.assertFalse(blocked)
        self.assertEqual(code, 1)

    def test_failed_cleanup_blocks_cli_status(self):
        with tempfile.TemporaryDirectory() as d:
            gate = Path(d) / 'active'; gate.mkdir()
            p = subprocess.run([sys.executable, m.__file__, 'status', '--state', d], capture_output=True,text=True)
            self.assertEqual(p.returncode, 1)
            self.assertEqual(p.stdout.strip(), 'blocked')
        code, r, blocked = self.run_guard([sys.executable, '-c', 'pass'], cleanup=False)
        self.assertTrue(blocked)
        self.assertFalse(r['cleanup_complete'])
        self.assertEqual(code, 1)

    def test_daemonized_child_in_owned_group_reaped(self):
        code, r, blocked = self.run_guard([sys.executable, '-c', 'import subprocess; subprocess.Popen(["sleep","30"])'])
        self.assertTrue(r['process_cleanup_complete'])
        self.assertFalse(blocked)

    def test_detached_guard_survives_controller_exit(self):
        import time
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)/'evidence'; root.mkdir()
            gate = Path(d)/'active'; gate.mkdir(); (gate/'owner.json').write_text('{}')
            guard_code = ("import sys; sys.path.insert(0, " + repr(str(Path(m.__file__).parent)) + "); "
                "import terminal_session as m; from pathlib import Path; "
                "m.terminal=lambda *a: 'closed'; m.tty_holders=lambda *a: []; "
                "m.guard(Path(" + repr(str(root)) + "),Path(" + repr(str(gate)) + "),'owned',2,"
                "[sys.executable,'-c','import time; time.sleep(.3)'])")
            controller = ("import subprocess,sys; subprocess.Popen([sys.executable,'-c'," + repr(guard_code) +
                "],stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,start_new_session=True)")
            subprocess.run([sys.executable,'-c',controller],check=True,timeout=2)
            deadline=time.monotonic()+5
            while not (root/'result.json').exists() and time.monotonic()<deadline: time.sleep(.05)
            self.assertTrue(json.loads((root/'result.json').read_text())['cleanup_complete'])
            self.assertFalse(gate.exists())


if __name__ == '__main__': unittest.main()
