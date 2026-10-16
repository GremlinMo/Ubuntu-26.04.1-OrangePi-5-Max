#!/usr/bin/python3
"""Install only reviewed report/benchmark discovery fixes, preserving originals."""
import hashlib
import os
from pathlib import Path
import shutil

if os.geteuid() != 0:
    raise SystemExit('Administrator installer only.')
source = Path('/home/oem/npu-integration-20261017-src')
backup = Path('/var/backups/orangepi-npu-integration-20261017')
targets = [('/usr/local/bin/orangepi-acceleration-report', '0282535af9df5203ba318b4f0e8ad6697e557975fd9bdb64615a94be97f0aaef', 0o755),
           ('/usr/share/orangepi-remix/report/test-video-throughput.py', '164eedbc8e9552b2ae055dab4ae66cc2a4a857423d233efb17d8f3c5e5ad9d3f', 0o644)]
for name, expected, mode in targets:
    target = Path(name)
    if hashlib.sha256(target.read_bytes()).hexdigest() != expected:
        raise SystemExit('Unexpected prior file: ' + name)
    if (backup / (target.name + '.before-decoder-discovery')).exists():
        raise SystemExit('Backup already exists.')
    compile((source / target.name).read_text(), name, 'exec')
for name, expected, mode in targets:
    target = Path(name)
    shutil.copy2(target, backup / (target.name + '.before-decoder-discovery'))
    temporary = target.with_name(target.name + '.npu-update')
    with temporary.open('xb') as stream:
        stream.write((source / target.name).read_bytes())
    temporary.chmod(mode)
    temporary.replace(target)
print('Updated report discovery; both prior files backed up. No driver changes.')
