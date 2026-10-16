#!/usr/bin/python3
"""Build, never install, an isolated ARM64 runtime from hash-pinned inputs."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import stat
import subprocess
import tarfile
import tempfile
import zipfile

VERSION = '1.0.0'
HERE = Path(__file__).resolve().parent
INPUTS = {
    'cpython-3.11.17+20261013-aarch64-unknown-linux-gnu-install_only_stripped.tar.gz':
        '3d09fa150bebc6c4f888f8d601328b46fd17f1be5c62cd390a353b7ccff6ed51',
    'tflite_runtime-2.14.0-cp311-cp311-manylinux_2_34_aarch64.whl':
        'ce9fa5d770a9725c746dcbf6f59f3178233b3759f09982e8b2db8d2234c333b0',
    'numpy-1.26.4-cp311-cp311-manylinux_2_17_aarch64.manylinux2014_aarch64.whl':
        '7ab55401287bfec946ced39700c053796e7cc0e3acbef09993a9ad2adba6ca6e',
    'pillow-11.3.0-cp311-cp311-manylinux2014_aarch64.manylinux_2_17_aarch64.whl':
        '7d1aa4de119a0ecac0a34a9c8bde33f34022e2e8f99104e47a3ca392fd60e37d',
    'mobilenet_v1_1.0_224_quant.tflite':
        'ecc3a67c47c5a609ec35f6a58a7d97532834e43df4cb7d3f1204a8164b7d20dd',
    'dog_224x224.jpg': 'c350299c6283d5f62fecf1f845b6b3be9aafec8dff528ca09a129990f0a584b0',
    'mesa-teflon-delegate_26.0.8-1ubuntu0.3_arm64.deb':
        'fdc23f047160690738b443dcd49f7074c463580b008d25e80321e240b4741386',
}
ASSETS = {
    'CORAL-LICENSE': 'f9946796a8a5bd5981565142fa42e3b0cc36aef6f80e86beaf5905b3c0fef1b5',
    'ROCKCHIP-LICENSE': '7fc60f3387179291c6f781d9e0931a30c710e34131699b7f5d3dfa2cfa5bb0c0',
    'imagenet_labels.txt': 'b8aaeb5630c62626a7d124a05c0e14230a7ffdd2136a31d0190a4fb71c1d82f1',
}


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def verify(root, expected):
    for name, digest in expected.items():
        if sha(root / name) != digest:
            raise RuntimeError('Unrecognized input: ' + name)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('assets', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    if platform.machine() != 'aarch64' or os.geteuid() == 0:
        raise RuntimeError('Build as a non-root user on ARM64 Linux.')
    verify(args.assets, INPUTS)
    verify(HERE / 'assets', ASSETS)
    args.output.mkdir(parents=True, exist_ok=True)
    output = args.output / ('orangepi-npu-runtime_' + VERSION + '_arm64.deb')
    if output.exists():
        raise RuntimeError('Output exists; choose a new output directory, do not overwrite releases.')
    with tempfile.TemporaryDirectory(prefix='orangepi-npu-build-') as staging:
        stage = Path(staging)
        package = stage / 'package'
        root = package / 'opt/orangepi-npu'
        root.mkdir(parents=True)
        with tarfile.open(args.assets / next(name for name in INPUTS if name.endswith('.tar.gz'))) as archive:
            if any(not entry.name.startswith('python/') for entry in archive.getmembers()):
                raise RuntimeError('Unexpected Python archive layout.')
            archive.extractall(root, filter='data')
        site = root / 'site-packages'
        site.mkdir()
        for name in INPUTS:
            if not name.endswith('.whl'):
                continue
            with zipfile.ZipFile(args.assets / name) as wheel:
                for member in wheel.infolist():
                    destination = (site / member.filename).resolve()
                    if not destination.is_relative_to(site) or stat.S_ISLNK(member.external_attr >> 16):
                        raise RuntimeError('Unexpected wheel path/link.')
                wheel.extractall(site)
        teflon = stage / 'teflon'
        subprocess.run(['dpkg-deb', '-x', str(args.assets / 'mesa-teflon-delegate_26.0.8-1ubuntu0.3_arm64.deb'),
                        str(teflon)], check=True)
        (root / 'lib').mkdir()
        shutil.copy2(teflon / 'usr/lib/teflon/libteflon.so', root / 'lib/libteflon.so')
        if sha(root / 'lib/libteflon.so') != '07586820f58e06168ce1afb8694955704a1d866de8d61fdcc9bc2b15d6844a98':
            raise RuntimeError('Delegate extraction mismatch.')
        shutil.copytree(HERE / 'assets', root / 'assets')
        for name in ('mobilenet_v1_1.0_224_quant.tflite', 'dog_224x224.jpg'):
            shutil.copy2(args.assets / name, root / 'assets' / name)
        for name in ('orangepi_npu.py', 'desktop.py', 'README.md', 'LICENSE'):
            shutil.copy2(HERE / name, root / name)
        shutil.copy2(teflon / 'usr/share/doc/mesa-teflon-delegate/copyright', root / 'assets/MESA-copyright')
        bins = package / 'usr/bin'
        bins.mkdir(parents=True)
        for command, script in [('orangepi-npu', 'orangepi_npu.py'), ('orangepi-npu-desktop', 'desktop.py')]:
            launcher = bins / command
            launcher.write_text('#!/bin/sh\nexec /opt/orangepi-npu/python/bin/python3.11 -I '
                                '/opt/orangepi-npu/' + script + ' "$@"\n')
            launcher.chmod(0o755)
        desktop = package / 'usr/share/applications'
        desktop.mkdir(parents=True)
        shutil.copy2(HERE / 'orangepi-npu.desktop', desktop / 'orangepi-npu.desktop')
        subprocess.run(['desktop-file-validate', str(desktop / 'orangepi-npu.desktop')], check=True)
        documentation = package / 'usr/share/doc/orangepi-npu-runtime'
        documentation.mkdir(parents=True)
        shutil.copy2(HERE / 'README.md', documentation / 'README.md')
        shutil.copy2(HERE / 'LICENSE', documentation / 'copyright')
        # Retain original archive modes for Python executables; disallow group/world writes.
        for path in package.rglob('*'):
            if path.is_symlink():
                if not path.resolve().is_relative_to(package):
                    raise RuntimeError('Package symlink escapes staging.')
                continue
            path.chmod(0o755 if path.is_dir() or path.stat().st_mode & 0o111 else 0o644)
        manifest = {'version': VERSION, 'inputs': INPUTS, 'label_assets': ASSETS,
                    'files': {str(p.relative_to(root)): sha(p) for p in sorted(root.rglob('*')) if p.is_file()}}
        (root / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
        control = package / 'DEBIAN'
        control.mkdir()
        installed_kb = sum(p.stat().st_size for p in package.rglob('*') if p.is_file()) // 1024
        (control / 'control').write_text(
            'Package: orangepi-npu-runtime\nVersion: ' + VERSION + '\nArchitecture: arm64\n'
            'Maintainer: Orange Pi Ubuntu community build <noreply@example.invalid>\n'
            'Section: science\nPriority: optional\nInstalled-Size: ' + str(installed_kb) + '\n'
            'Depends: libc6 (>= 2.38), libdrm2 (>= 2.4.125), libexpat1, libzstd1, zlib1g, libgcc-s1, libstdc++6, zenity\n'
            'Description: Isolated Rocket/Teflon NPU classifier for the Orange Pi 5 Max\n'
            ' Pinned Python/TFLite runtime and MobileNet V1 example. No kernel, graphics\n'
            ' or system Python replacement. Requires an existing Rocket driver.\n')
        subprocess.run(['dpkg-deb', '--root-owner-group', '-Zxz', '-z3', '--build', str(package), str(output)], check=True)
    print(json.dumps({'package': str(output), 'sha256': sha(output), 'version': VERSION}))


if __name__ == '__main__':
    main()
