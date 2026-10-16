#!/usr/bin/python3
"""Selective, reversible APT protection for the tested Orange Pi hardware stack."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tarfile
import apt

STATE = Path('/var/lib/orangepi-update-guard/state.json')
CONF = Path('/etc/apt/apt.conf.d/52orangepi-hardware-guard')
BACKUP = Path('/var/backups/orangepi-update-guard-20261017')
SOURCES = {'mesa', 'gstreamer1.0', 'gst-plugins-base1.0', 'gst-plugins-bad1.0', 'gst-plugins-extra1.0'}
EXACT = {'bcmdhd-sdio-dkms', 'orangepi-npu-runtime', 'linux-firmware',
         'linux-firmware-broadcom-wireless', 'linux-firmware-misc', 'linux-firmware-realtek'}


def command(*args):
    return subprocess.check_output(args, text=True).strip()


def canonical(name):
    return name.split(':')[0]


def selected(name, source):
    if name in EXACT:
        return 'board firmware/runtime'
    if source in SOURCES:
        return 'tested graphics/video'
    if re.fullmatch(r'linux-(?:image|headers|modules|modules-extra|main-modules-zfs)-[0-9].*', name):
        return 'installed kernel/recovery'
    if re.fullmatch(r'linux-(?:generic|image-generic|headers-generic)(?:-hwe-[0-9.]+)?', name):
        return 'kernel update metapackage'
    return None


def inventory():
    cache = apt.Cache()
    rows = []
    for package in cache:
        if not package.is_installed:
            continue
        reason = selected(package.name, package.installed.source_name)
        if reason:
            rows.append({'name': package.name, 'version': package.installed.version,
                         'source': package.installed.source_name, 'reason': reason,
                         'auto': package.is_auto_installed})
    return sorted(rows, key=lambda row: row['name'])


def generated_config(rows):
    # Anchored exact-name regexes; append to existing lists, never clear security origins.
    names = [re.escape(row['name']) for row in rows]
    kernels = [re.escape(row['name']) for row in rows if row['reason'].startswith(('installed kernel', 'kernel update'))]
    return ('// Managed by orangepi-update-guard. Review held security fixes regularly.\n'
            'Unattended-Upgrade::Package-Blacklist {\n' +
            ''.join('  "^' + name + '$";\n' for name in names) + '};\n'
            'APT::NeverAutoRemove {\n' + ''.join('  "^' + name + '$";\n' for name in kernels) + '};\n')


def write_json(path, data):
    temporary = path.with_suffix('.new')
    with temporary.open('x') as stream:
        json.dump(data, stream, indent=2)
        stream.write('\n')
    temporary.chmod(0o644)
    temporary.replace(path)


def read_state():
    if not STATE.exists():
        raise RuntimeError('No managed policy installed.')
    return json.loads(STATE.read_text())


def status(review=False):
    state = read_state()
    holds = {canonical(name) for name in command('apt-mark', 'showhold').splitlines()}
    cache = apt.Cache()
    rows = []
    for saved in state['packages']:
        name = saved['name']
        package = cache[name]
        row = {'name': name, 'held': name in holds, 'tested_version': saved['version'],
               'installed': package.installed.version if package.is_installed else None}
        if review:
            row['candidate'] = package.candidate.version if package.candidate else None
            row['newer_candidate'] = package.is_upgradable
        rows.append(row)
    intact = CONF.exists() and hashlib.sha256(CONF.read_bytes()).hexdigest() == state['config_sha256']
    report = {'active': state['active'], 'config_intact': intact, 'packages': rows,
              'security_warning': 'Protected packages also defer their security updates. Review regularly.',
              'scope': 'APT package operations, not Snap refreshes, distribution upgrades, direct dpkg/forced installs or manual file writes.'}
    print(json.dumps(report, indent=2))
    return 0 if not state['active'] or intact and all(r['held'] and r['installed'] == r['tested_version'] for r in rows) else 1


def enable():
    if os.geteuid() != 0:
        raise RuntimeError('Enable requires sudo; status/review do not.')
    if STATE.exists():
        state = read_state()
        if state['active']:
            return status()
        if CONF.exists():
            raise RuntimeError('Configuration exists while inactive; inspect first.')
        cache = apt.Cache()
        if any(not cache[r['name']].is_installed or cache[r['name']].installed.version != r['version'] for r in state['packages']):
            raise RuntimeError('Versions changed since qualification; review and requalify before replacing the baseline.')
        previous = {canonical(name) for name in command('apt-mark', 'showhold').splitlines()}
        state['prior_holds'] = sorted(previous)
        state['new_holds'] = sorted({r['name'] for r in state['packages']} - previous)
        state['new_manual'] = [r['name'] for r in state['packages'] if cache[r['name']].is_auto_installed and r['reason'].startswith(('installed kernel', 'kernel update'))]
        with CONF.open('x') as stream:
            stream.write(generated_config(state['packages']))
        CONF.chmod(0o644)
        if state['new_holds']:
            command('apt-mark', 'hold', *state['new_holds'])
        if state['new_manual']:
            command('apt-mark', 'manual', *state['new_manual'])
        state['active'] = True
        write_json(STATE, state)
        return status()
    if CONF.exists() or BACKUP.exists():
        raise RuntimeError('Existing policy or backup; inspect rather than overwrite.')
    if os.uname().release != '7.0.0-38-generic':
        raise RuntimeError('This initial policy must be reviewed for the currently tested kernel.')
    rows = inventory()
    names = [row['name'] for row in rows]
    if not {'bcmdhd-sdio-dkms', 'orangepi-npu-runtime', 'linux-image-7.0.0-38-generic'} <= set(names):
        raise RuntimeError('Expected custom stack is incomplete.')
    previous = {canonical(name) for name in command('apt-mark', 'showhold').splitlines()}
    text = generated_config(rows)
    state = {'active': False, 'created': datetime.datetime.now(datetime.timezone.utc).isoformat(),
             'packages': rows, 'prior_holds': sorted(previous),
             'new_holds': sorted(set(names) - previous),
             'new_manual': [r['name'] for r in rows if r['auto'] and r['reason'].startswith(('installed kernel', 'kernel update'))],
             'config_sha256': hashlib.sha256(text.encode()).hexdigest()}
    BACKUP.mkdir(mode=0o700, parents=True)
    (BACKUP / 'prior-state.json').write_text(json.dumps(state, indent=2) + '\n')
    # No home/profile/network credentials. A boot-file recovery copy is not a full disk backup.
    paths = [Path('/boot'), Path('/etc/dracut.conf.d'), Path('/etc/modprobe.d'),
             Path('/etc/systemd/system/orangepi-wifi-ready.service'),
             Path('/usr/local/sbin/orangepi-wifi-ready'),
             Path('/usr/lib/firmware/SYN43711A0.hcd'),
             Path('/usr/lib/firmware/brcm/BCM.xunlong,orangepi-5-max.hcd')]
    with tarfile.open(BACKUP / 'boot-and-board-files.tar.gz', 'x:gz') as archive:
        for path in paths:
            if path.exists():
                archive.add(path, arcname=str(path).lstrip('/'))
    STATE.parent.mkdir(mode=0o755, parents=True, exist_ok=True)
    write_json(STATE, state)
    try:
        with CONF.open('x') as stream:
            stream.write(text)
        CONF.chmod(0o644)
        command('apt-config', 'dump')
        command('apt-mark', 'hold', *state['new_holds'])
        if state['new_manual']:
            command('apt-mark', 'manual', *state['new_manual'])
        state['active'] = True
        write_json(STATE, state)
    except Exception:
        if state['new_holds']:
            command('apt-mark', 'unhold', *state['new_holds'])
        if state['new_manual']:
            command('apt-mark', 'auto', *state['new_manual'])
        if CONF.exists() and hashlib.sha256(CONF.read_bytes()).hexdigest() == state['config_sha256']:
            CONF.unlink()
        raise
    return status()


def disable():
    if os.geteuid() != 0:
        raise RuntimeError('Disable requires sudo.')
    state = read_state()
    if not state['active']:
        raise RuntimeError('Policy is already inactive.')
    if not CONF.exists() or hashlib.sha256(CONF.read_bytes()).hexdigest() != state['config_sha256']:
        raise RuntimeError('Managed configuration changed; refusing automatic removal.')
    if state['new_holds']:
        command('apt-mark', 'unhold', *state['new_holds'])
    if state['new_manual']:
        command('apt-mark', 'auto', *state['new_manual'])
    CONF.unlink()
    state['active'] = False
    write_json(STATE, state)
    print('Managed protection removed. Pre-existing holds preserved. No package updates installed. Backup retained.')
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('plan', 'enable', 'status', 'review', 'disable'))
    args = parser.parse_args()
    if args.action == 'plan':
        print(json.dumps({'packages': inventory(), 'configuration': generated_config(inventory())}, indent=2))
        return 0
    if args.action == 'enable':
        return enable()
    if args.action == 'disable':
        return disable()
    return status(args.action == 'review')


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except Exception as error:
        raise SystemExit('Update guard: ' + str(error))
