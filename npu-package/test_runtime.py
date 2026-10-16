"""Hardware-free behavior checks; real ARM64 qualification is separate."""
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import json

spec = importlib.util.spec_from_file_location('npu', Path(__file__).with_name('orangepi_npu.py'))
npu = importlib.util.module_from_spec(spec)
spec.loader.exec_module(npu)
desktop_spec = importlib.util.spec_from_file_location('desktop', Path(__file__).with_name('desktop.py'))
desktop = importlib.util.module_from_spec(desktop_spec)
desktop_spec.loader.exec_module(desktop)


class RuntimeTests(unittest.TestCase):
    def test_correct_comparison(self):
        self.assertTrue(npu.compare_outputs([0, 252, 3], [0, 252, 2])['passed'])

    def test_wrong_class_rejected(self):
        self.assertFalse(npu.compare_outputs([0, 20, 19], [0, 19, 20])['passed'])

    def test_large_difference_rejected(self):
        self.assertFalse(npu.compare_outputs([0, 252, 3], [0, 252, 7])['passed'])

    def test_wrong_shape_rejected(self):
        with self.assertRaises(RuntimeError):
            npu.compare_outputs([1], [1, 2])

    def test_checksum_tampering_rejected(self):
        with tempfile.TemporaryDirectory(prefix='npu-unit-test-', dir=Path(__file__).resolve().parent) as folder:
            root = Path(folder)
            (root / 'asset').write_bytes(b'original')
            (root / 'manifest.json').write_text(json.dumps({'files': {'asset': npu.digest(root/'asset')}}))
            with patch.object(npu, 'ROOT', root):
                npu.verify_files()
                (root / 'asset').write_bytes(b'changed')
                with self.assertRaises(RuntimeError):
                    npu.verify_files()

    def test_no_node_fails(self):
        with patch.object(npu.platform, 'machine', return_value='aarch64'), patch.object(npu.Path, 'exists', return_value=True), patch.object(npu.os, 'access', return_value=False):
            with self.assertRaisesRegex(RuntimeError, 'permission denied'):
                npu.device_check()

    def test_doctor_does_not_claim_inference(self):
        self.assertIn('No inference', npu.format_report({'action': 'doctor', 'version': '1', 'kernel': 'test'}))

    def test_desktop_cancel_does_not_run_inference(self):
        from types import SimpleNamespace
        with patch.object(desktop.subprocess, 'run', return_value=SimpleNamespace(returncode=1)) as run:
            desktop.main()
            self.assertEqual(run.call_count, 1)

    def test_desktop_image_argument_is_not_shell_text(self):
        from types import SimpleNamespace
        replies = [SimpleNamespace(returncode=0, stdout='Classify an image\n'),
                   SimpleNamespace(returncode=0, stdout='/tmp/a photo; safe.jpg\n'),
                   SimpleNamespace(returncode=0, stdout='PASS', stderr=''),
                   SimpleNamespace(returncode=0)]
        with patch.object(desktop.subprocess, 'run', side_effect=replies) as run, patch.object(desktop.subprocess, 'Popen'):
            desktop.main()
            self.assertEqual(run.call_args_list[2].args[0][-2:], ['--', '/tmp/a photo; safe.jpg'])
            self.assertNotIn('shell', run.call_args_list[2].kwargs)


if __name__ == '__main__':
    unittest.main()
