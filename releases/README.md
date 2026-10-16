# Binary release status

No current ISO or all-in-one binary driver bundle is published yet.

The development board has verified GPU rendering, native video decode, 5-GHz
Wi-Fi, Bluetooth pairing/A2DP and NPU inference. The historical October 13 image
does not include subsequent fixes and is not a current release candidate.

## Required before a public image download

- Build a fresh regular-file disk image; never publish a raw dump of the live
  mounted root filesystem or erase the development eMMC.
- Preserve current tested kernel/initrd/DTB, Bluetooth 1.5-Mbaud configuration,
  Wi-Fi readiness service, NPU runtime, desktop fixes and update protection.
- Remove user homes, passwords other than the declared default, SSH keys,
  Wi-Fi secrets, Bluetooth bonds, machine identity, logs and development state.
  Inspect initramfs and embedded archives as well as ordinary filesystem paths.
- Validate partition IDs, boot entries, filesystem consistency, package state,
  first-boot identity regeneration, checksums and payload contents.
- Resolve exact firmware redistribution permission, package source obligations,
  third-party notices and modified-Ubuntu branding requirements.
- Physically flash and boot-test a fresh installation before claiming fresh-image
  boot validation. Development-board results alone do not prove that export.

The intended ISO contains an inner `.img.gz`, matching drivers, instructions and
checksums. It is **not** a bootable UEFI installer. GitHub release assets must each
be under 2 GiB, so a larger ISO will need numbered parts with verified reassembly
instructions. Do not flash an ISO part or the assembled container itself.

The October 17 candidate's convenience credentials are `oem` / `orangepi`, with
root password login disabled. The default password was checked in the candidate
filesystem; fresh-device login/boot testing remains outstanding.
Change the password immediately and never expose
default-password SSH to an untrusted network. No such credentials grant access
to a user's private Wi-Fi or online accounts.

The original Ubuntu installer ISO and original vendor Arch image are excluded.
