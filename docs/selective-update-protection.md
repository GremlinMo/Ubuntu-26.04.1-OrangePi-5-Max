# Selective update protection — enabled 2026-10-17

ENABLED on the development Ubuntu Pi after explicit user approval to retry.
All 43 package holds and their exact tested versions were verified, including the
pre-existing bcmdhd-sdio-dkms hold. No updates were installed and no reboot occurred.
The earlier safety-review block is resolved. This protection is on the running Pi;
the previously exported ISO has not been rebuilt to include it.

## Exact protected package list

Board-specific runtime and relevant firmware (6):

```
bcmdhd-sdio-dkms
orangepi-npu-runtime
linux-firmware
linux-firmware-broadcom-wireless
linux-firmware-misc
linux-firmware-realtek
```

Tested Mesa graphics family (6):

```
libegl-mesa0
libgbm1
libgl1-mesa-dri
libglx-mesa0
mesa-libgallium
mesa-vulkan-drivers
```

Matched GStreamer core/base/hardware-decoder family (15):

```
gir1.2-gst-plugins-base-1.0
gir1.2-gstreamer-1.0
gstreamer1.0-alsa
gstreamer1.0-gl
gstreamer1.0-plugins-bad
gstreamer1.0-plugins-base
gstreamer1.0-plugins-base-apps
gstreamer1.0-plugins-extra
gstreamer1.0-tools
gstreamer1.0-x
libgstreamer-gl1.0-0
libgstreamer-plugins-bad1.0-0
libgstreamer-plugins-base1.0-0
libgstreamer-plugins-extra1.0-0
libgstreamer1.0-0
```

Installed kernels, matching modules/headers and tracking metapackages (16):

```
linux-generic-hwe-24.04
linux-generic-hwe-26.04
linux-headers-7.0.0-30
linux-headers-7.0.0-30-generic
linux-headers-7.0.0-38
linux-headers-7.0.0-38-generic
linux-headers-generic
linux-headers-generic-hwe-26.04
linux-image-7.0.0-30-generic
linux-image-7.0.0-38-generic
linux-image-generic
linux-image-generic-hwe-26.04
linux-main-modules-zfs-7.0.0-30-generic
linux-main-modules-zfs-7.0.0-38-generic
linux-modules-7.0.0-30-generic
linux-modules-7.0.0-38-generic
```

## Effect and limitations

- Hold these installed versions for ordinary APT operations. Add exact-package
  unattended-upgrade exclusions; keep existing security origins and periodic
  update settings unchanged.
- Keep the protected kernel packages manually installed and excluded from
  autoremove. Preserve the pre-existing Wi-Fi hold when disabling the policy.
- Back up boot files and selected board configuration before enabling. This is
  not a full disk backup or complete package rollback image.
- Do not hold Firefox, OpenSSL, glibc, BlueZ, PipeWire, ALSA UCM, libmp3lame0 or
  ordinary applications. GStreamer's ALSA plugin is part of its matched base
  family above, distinct from holding the system audio stack.
- Dependency constraints can still defer other updates. No blanket guarantee
  that every unrelated update will install is made.
- Held packages ALSO miss automatic security fixes. Review regularly; qualified
  kernel/Mesa/video updates should be tested and deliberately adopted, not frozen
  forever. The private NPU runtime needs its own maintenance too.
- This is not protection against explicit forced installs, direct dpkg usage,
  distribution upgrades or manual file changes. Firefox Snap and its graphics
  content runtime remain separately updated by Snap.

Source is `../scripts/orangepi-update-guard.py`, installed as
`/usr/local/sbin/orangepi-update-guard`. Commands on the Pi:

```
orangepi-update-guard status
orangepi-update-guard review
sudo orangepi-update-guard disable
sudo orangepi-update-guard enable
```

Disabling removes only this policy's added holds, preserves the old Wi-Fi hold,
and restores kernel automatic-install flags that this policy changed. It does
not install updates. Review uses cached package metadata, not
an automatic network refresh. Re-enabling after actual version changes refuses
to bless a new baseline without requalification. No scheduled monitor is created.

APT hold behavior: https://manpages.ubuntu.com/manpages/resolute/man8/apt-mark.8.html

## Completed live verification

`../scripts/test-update-guard.py` passed on the Pi. The read-only live validator
`../scripts/validate-update-guard.py` then passed:

- All 43 holds and installed versions match; managed configuration hash is intact.
- Parsed unattended-upgrade exclusions match protected package names and do not
  match Firefox, OpenSSL, glibc, BlueZ, PipeWire, ALSA UCM or libmp3lame0.
- Update-Package-Lists and Unattended-Upgrade periodic settings remain `1`.
  Ubuntu release/security and ESM security origins remain configured.
- `apt-get -s upgrade` and `apt-get -s dist-upgrade`: each succeeds, plans 85
  package installs/upgrades and zero removals, with zero protected changes.
- `apt-get -s autoremove`: succeeds, proposes eight unrelated removals and zero
  protected changes. Nothing was actually removed.
- Root-only backup directory `/var/backups/orangepi-update-guard-20261017`
  contains prior state plus a readable 116,791,748-byte boot/board archive with
  73 entries, including extlinux configuration and no home/network profiles.

State: `/var/lib/orangepi-update-guard/state.json`.
APT configuration: `/etc/apt/apt.conf.d/52orangepi-hardware-guard`.
Simulations used the current cached package lists. Disable/re-enable was not
exercised on the live board, to avoid temporarily dropping protection.
