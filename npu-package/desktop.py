#!/usr/bin/env python3
"""Small desktop entry using the existing Zenity installation; no root or network."""
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent


def main():
    choice = subprocess.run(['zenity', '--list', '--title=Orange Pi NPU', '--width=560', '--height=320',
        '--text=Run the RK3588 NPU locally. First use may compile the model for several seconds.',
        '--column=Action', 'Verify NPU against CPU', 'Classify an image', 'Run bundled demo', 'Runtime health check'],
        capture_output=True, text=True)
    if choice.returncode:
        return
    action = {'Verify NPU against CPU': 'verify', 'Classify an image': 'classify',
              'Run bundled demo': 'demo', 'Runtime health check': 'doctor'}[choice.stdout.strip()]
    command = [sys.executable, '-I', str(ROOT / 'orangepi_npu.py'), action]
    if action == 'classify':
        image = subprocess.run(['zenity', '--file-selection', '--title=Choose an image for local NPU classification'],
                               capture_output=True, text=True)
        if image.returncode:
            return
        command += ['--', image.stdout.rstrip('\n')]
    progress = subprocess.Popen(['zenity', '--progress', '--pulsate', '--no-cancel', '--auto-close',
        '--title=Orange Pi NPU', '--text=Running locally; please wait...'], stdin=subprocess.PIPE,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, text=True)
    try:
        child = subprocess.run(command, capture_output=True, text=True, timeout=130)
        message = child.stdout if child.returncode == 0 else (child.stderr + '\n' + child.stdout)[-6000:]
    except Exception as error:
        message = str(error)
    finally:
        progress.communicate('100\n', timeout=10)
    subprocess.run(['zenity', '--text-info', '--title=Orange Pi NPU result', '--width=760', '--height=520'],
                   input=message, text=True)


if __name__ == '__main__':
    main()
