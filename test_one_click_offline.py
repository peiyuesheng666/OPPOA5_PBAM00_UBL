"""Offline checks: no serial connections or handset mutations."""

if __name__ == "__main__":
    print('解锁方案/脚本/文件 By 酷安@Dev裴月笙 公益解锁文件，禁止倒卖盈利', flush=True)

import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import one_click_unlock as app


class WorkflowChecks(unittest.TestCase):
    def test_real_a03_gpt(self):
        path = app.ROOT.parent / 'verify-after-a03'
        candidates = list(path.glob('*gpt*.bin'))
        if not candidates:
            self.skipTest('No local GPT fixture')
        parts = app.parse_gpt(candidates[0].read_bytes())
        self.assertEqual(parts['boot'], (597216, 728287))

    def test_corrupt_gpt_stops(self):
        with self.assertRaises(RuntimeError):
            app.parse_gpt(bytes(34 * 512))

    def test_fresh_backend_result_required(self):
        fixture = app.load(app.ROOT / 'partition-analysis/ram-unlock-trace11/observed-sahara-trace.json')
        self.assertTrue(app.unlocked(fixture))
        for key, value in [('return_raw', '0xffffffff'), ('main_unlocked', 0),
                           ('header_magic_valid', False), ('returned', False)]:
            bad = copy.deepcopy(fixture)
            bad['aboot_trace']['backend'][key] = value
            self.assertFalse(app.unlocked(bad))
        self.assertFalse(app.unlocked({}))

    def test_failed_stage_never_launches(self):
        with tempfile.TemporaryDirectory() as folder:
            directory = Path(folder)
            (directory / 'stage-sbl-verification.json').write_text(json.dumps(
                {'full_readback_verified': False, 'error': 'simulated transport failure'}))
            with patch.object(app, 'run_command') as run:
                with self.assertRaises(RuntimeError):
                    app.execute_stage(directory)
                self.assertEqual(run.call_count, 1)

    def test_wrong_firmware_stops(self):
        rows = app.load(app.ROOT / 'firmware-a03-required.json')
        parts = {r['label']: (100, 100 + (r['bytes']+511)//512) for r in rows}
        with tempfile.TemporaryDirectory() as folder:
            with patch.object(app, 'parse_gpt', return_value=parts), \
                 patch.object(app, 'read_sectors', return_value=b'wrong firmware'):
                with self.assertRaisesRegex(RuntimeError, 'A.03'):
                    app.verify_firmware('COM_FAKE', Path(folder))


if __name__ == '__main__':
    unittest.main()
