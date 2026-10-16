#!/usr/bin/python3
"""Non-root validation of the installed package; no raw traces are saved."""
import json
import os
from pathlib import Path
import re
import subprocess
import sys


def run(command, **kwargs):
    child = subprocess.run(command, text=True, capture_output=True, timeout=150, **kwargs)
    if child.returncode:
        raise RuntimeError('Command failed: ' + ' '.join(command) + '\n' + (child.stdout+child.stderr)[-4000:])
    return child


def main():
    if os.geteuid() == 0:
        raise RuntimeError('Qualification must run as an ordinary user.')
    doctor = json.loads(run(['orangepi-npu', 'doctor', '--json']).stdout)
    environment = dict(os.environ, TEFLON_DEBUG='verbose')
    traced = run(['strace', '-f', '-yy', '-e', 'trace=openat,ioctl',
                  'orangepi-npu', 'demo', '--runs', '3', '--json'], env=environment)
    submits = []
    for line in traced.stderr.splitlines():
        if '/dev/accel/accel0' not in line or 'ioctl(' not in line:
            continue
        if ('DRM_IOCTL_ROCKET_SUBMIT' in line or '0x40186441' in line or
                re.search(r'_IOC\(_IOC_WRITE,\s*0x64,\s*0x41,\s*0x18\)', line)):
            submits.append(line)
    proof = {'successful_rocket_submits': sum(bool(re.search(r'= 0\s*$', line)) for line in submits),
             'failed_or_unparsed_submits': sum(not bool(re.search(r'= 0\s*$', line)) for line in submits),
             'rocket_loaded_log': 'loaded rocket driver' in traced.stdout + traced.stderr,
             'raw_trace_saved': False}
    if proof['successful_rocket_submits'] == 0 or proof['failed_or_unparsed_submits']:
        raise RuntimeError('No clean hardware submission evidence: ' + json.dumps(proof))
    # Explicit per-process A76 affinity for comparable CPU/NPU latency; no governor changes.
    if 4 not in os.sched_getaffinity(0):
        raise RuntimeError('Expected A76 CPU4 unavailable for matched comparison.')
    verification = json.loads(run(['taskset', '-c', '4', 'orangepi-npu', 'verify', '--runs', '20', '--json']).stdout)
    classification = json.loads(run(['orangepi-npu', 'classify',
        '/opt/orangepi-npu/assets/dog_224x224.jpg', '--runs', '1', '--json']).stdout)
    invalid = subprocess.run(['orangepi-npu', 'classify', '/nonexistent/npu-test-image.jpg'],
                             capture_output=True, text=True, timeout=30)
    if invalid.returncode == 0:
        raise RuntimeError('Missing image unexpectedly accepted.')
    report = {'doctor': doctor, 'hardware_proof': proof, 'verification': verification,
              'classification': classification, 'missing_image_rejected': True,
              'system_uid': os.geteuid(), 'kernel': os.uname().release,
              'note': 'No clock, voltage, boot, permission or system-library changes made by qualification.'}
    destination = Path(sys.argv[1])
    with destination.open('x') as stream:
        json.dump(report, stream, indent=2)
        stream.write('\n')
    print(json.dumps(report), flush=True)


if __name__ == '__main__':
    main()
