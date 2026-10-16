#!/usr/bin/python3
"""Read-only checks of update-policy selection and exact matching."""
import importlib.util
from pathlib import Path
import re

spec = importlib.util.spec_from_file_location('guard', Path(__file__).with_name('orangepi-update-guard.py'))
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)
for name in ['linux-image-7.0.0-38-generic', 'linux-headers-7.0.0-38', 'linux-image-generic-hwe-26.04',
             'bcmdhd-sdio-dkms', 'orangepi-npu-runtime']:
    assert guard.selected(name, 'unrelated') is not None, name
for name in ['firefox', 'openssl', 'libc6', 'pipewire', 'bluez', 'alsa-ucm-conf', 'linux-libc-dev', 'linux-perf', 'libmp3lame0']:
    assert guard.selected(name, 'unrelated') is None, name
assert guard.selected('libgbm1', 'mesa')
assert guard.selected('libgstreamer1.0-0', 'gstreamer1.0')
text = guard.generated_config([{'name': 'linux-image-7.0.0-38-generic', 'reason': 'installed kernel/recovery'}])
pattern = re.findall(r'"(.*?)"', text)[0]
assert re.fullmatch(pattern, 'linux-image-7.0.0-38-generic')
assert not re.fullmatch(pattern, 'linux-image-7x0x0-38-generic')
assert not re.fullmatch(pattern, 'linux-image-7.0.0-38-generic-extra')
assert '#clear' not in text and 'Allowed-Origins' not in text and 'Periodic' not in text
print('Selection, unrelated-package exclusions, anchored regex and security-origin preservation checks passed.')
