#!/usr/bin/python3
"""Back up and install the reviewed report update; refuse unexpected prior edits."""
import hashlib
import os
from pathlib import Path
import shutil
import sys

source = Path(sys.argv[1])
target = Path('/usr/local/bin/orangepi-acceleration-report')
backup = Path('/var/backups/orangepi-npu-integration-20261017/orangepi-acceleration-report')
if os.geteuid() != 0:
    raise SystemExit('Installer requires administrator privileges, not the runtime.')
if hashlib.sha256(target.read_bytes()).hexdigest() != '109d6e7648205695c4bf3ad6c25b5e4f1adfbffdbabe45a0fd7ae5678b6f8924':
    raise SystemExit('Report changed since inspection; refusing overwrite.')
compile(source.read_text(), str(target), 'exec')
if backup.exists():
    raise SystemExit('Backup exists; inspect rather than overwrite.')
backup.parent.mkdir(mode=0o755, parents=True, exist_ok=True)
shutil.copy2(target, backup)
temporary = target.with_name(target.name + '.npu-integration-new')
with temporary.open('xb') as stream:
    stream.write(source.read_bytes())
temporary.chmod(0o755)
temporary.replace(target)
print('Report updated; original backed up at ' + str(backup))
