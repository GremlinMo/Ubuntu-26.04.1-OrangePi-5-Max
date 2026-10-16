#!/usr/bin/python3
"""Build a single-property Bluetooth baud DTB candidate; never select its boot entry."""
import hashlib
import json
from pathlib import Path
import runpy
import shutil
import struct
import subprocess

source = Path('/boot/dtbs/rockchip/rk3588-orangepi-5-max-ap6611-resolved-150mhz.dtb')
output = Path('/home/oem/rk3588-orangepi-5-max-ap6611-bt1500000-20261014.dtb')
expected = 'c4bb91335053fa582af6ce2eb17ad39fcf1d580c4abcdf0d10eb596ec4b4056f'
if hashlib.sha256(source.read_bytes()).hexdigest() != expected:
    raise SystemExit('Unexpected base DTB; no candidate generated.')
if output.exists():
    raise SystemExit('Candidate already exists; inspect rather than overwrite.')
parse = runpy.run_path(str(Path(__file__).with_name('audit-ap6611-dtb.py')))['parse']
before = parse(source)
matches = [node for node, values in before.items()
           if values.get('compatible') == b'brcm,bcm43438-bt\0']
if len(matches) != 1 or not matches[0].startswith('/serial@feba0000/'):
    raise SystemExit('Unexpected Bluetooth node; no candidate generated.')
node = matches[0]
if 'max-speed' in before[node]:
    raise SystemExit('Base already sets max-speed; inspect first.')
shutil.copyfile(source, output)
subprocess.run(['fdtput', '-t', 'u', str(output), node, 'max-speed', '1500000'], check=True)
after = parse(output)
changed = [path for path in before.keys() | after.keys() if before.get(path) != after.get(path)]
expected_properties = dict(before[node], **{'max-speed': struct.pack('>I', 1500000)})
if changed != [node] or after[node] != expected_properties:
    raise RuntimeError('Candidate has unexpected semantic changes; do not deploy.')
print(json.dumps({'candidate': str(output), 'changed_nodes': changed,
    'only_changed_property': 'max-speed', 'baud': 1500000,
    'all_other_nodes_and_properties_identical': True,
    'source_sha256': expected, 'candidate_sha256': hashlib.sha256(output.read_bytes()).hexdigest(),
    'boot_selection_changed': False, 'kernel_initrd_firmware_wifi_and_gpu_unchanged': True}), flush=True)
