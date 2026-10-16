#!/usr/bin/python3
"""Read-only live verification; all APT operations are simulations."""
import json
from pathlib import Path
import re
import subprocess
import tarfile
import apt_pkg

apt_pkg.init()
state = json.loads(Path('/var/lib/orangepi-update-guard/state.json').read_text())
protected = {r['name'] for r in state['packages']}
status = json.loads(subprocess.check_output(
    ['/usr/local/sbin/orangepi-update-guard', 'status'], text=True))
holds = set(subprocess.check_output(['apt-mark', 'showhold'], text=True).split())
patterns = apt_pkg.config.value_list('Unattended-Upgrade::Package-Blacklist')
kernels = apt_pkg.config.value_list('APT::NeverAutoRemove')
matches = lambda name, rules: any(re.search(rule, name) for rule in rules)
assert state['active'] and status['config_intact']
assert len(protected) == 43
assert set(state['prior_holds']) <= holds
assert all(matches(name, patterns) for name in protected)
unrelated = ['firefox', 'openssl', 'libc6', 'bluez', 'pipewire', 'alsa-ucm-conf', 'libmp3lame0']
assert not any(matches(name, patterns) for name in unrelated)
assert all(matches(r['name'], kernels) for r in state['packages']
           if r['reason'].startswith(('installed kernel', 'kernel update')))
periodic = {name: apt_pkg.config.find('APT::Periodic::' + name)
            for name in ['Update-Package-Lists', 'Unattended-Upgrade']}
assert all(value == '1' for value in periodic.values()), periodic
simulations = {}
for action in ['upgrade', 'dist-upgrade', 'autoremove']:
    result = subprocess.run(['apt-get', '-s', action], text=True, capture_output=True)
    changes = re.findall(r'^(Inst|Remv) ([^ :]+)', result.stdout, re.M)
    conflicts = [name for _, name in changes if name in protected]
    simulations[action] = {'exit_code': result.returncode,
                           'planned_installs': sum(kind == 'Inst' for kind, _ in changes),
                           'planned_removals': sum(kind == 'Remv' for kind, _ in changes),
                           'protected_changes': conflicts,
                           'summary': [line for line in result.stdout.splitlines()
                                       if 'upgraded,' in line],
                           'stderr': result.stderr.strip()}
    assert result.returncode == 0 and not conflicts, simulations[action]
backup = Path('/var/backups/orangepi-update-guard-20261017/boot-and-board-files.tar.gz')
with tarfile.open(backup, 'r:gz') as archive:
    names = archive.getnames()
    assert 'boot/extlinux/extlinux.conf' in names
    assert not any(name.startswith(('home/', 'etc/NetworkManager/system-connections')) for name in names)
print(json.dumps({'passed': True, 'protected_count': len(protected),
                  'prior_holds_preserved': True, 'exact_blacklist_matches': True,
                  'periodic': periodic,
                  'allowed_origins': apt_pkg.config.value_list('Unattended-Upgrade::Allowed-Origins'),
                  'simulations': simulations,
                  'backup_bytes': backup.stat().st_size, 'backup_entries': len(names)}, indent=2))
