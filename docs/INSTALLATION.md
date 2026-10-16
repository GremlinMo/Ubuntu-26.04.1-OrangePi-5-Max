# Installation guide

## Release status — read first

The current repository is a source/development preview. A new image candidate
is being prepared; no current binary image is publicly released or proven by a
fresh-device boot. Do not use the older October 13 image as though it contains
the current Bluetooth, NPU, desktop and update-protection changes.

These instructions describe the intended **eMMC** image workflow. They do not
establish boot support for SD, NVMe or USB, and are not a generic ARM installer.

## What you need

- An **Orange Pi 5 Max**, stable appropriate power and cooling.
- A backup of all data on the target, plus a working board-specific recovery SD.
- Target eMMC large enough for the **uncompressed** image. The current candidate
  is 12 GiB; a nominal 16-GB-or-larger eMMC has sufficient raw capacity. Follow
  the final release's requirements rather than the compressed download size.
- A Windows, Linux or macOS PC and a compatible USB eMMC reader, if the module
  can be removed safely. Do not fit/remove storage while the Pi is powered.
- **[balenaEtcher](https://etcher.balena.io/)** from its official site. Its
  [official test documentation](https://etcher-docs.balena.io/MANUAL-TESTING/)
  includes GZ-image flashing; decompression to `.img` is an alternative.

Do not use Etcher to write the packaging ISO, any numbered ISO part, the
original Ubuntu ARM64 ISO, or a source-code archive.

## 1. Obtain and verify the release

Use this repository's Releases page once a current image is published. Download
the supplied SHA256 manifest and every required image/ISO part. Follow that
release's exact reassembly instructions; partial downloads cannot be flashed.
The assembled ISO may exceed FAT32's single-file limit, so use NTFS, exFAT or
a suitable Linux filesystem for downloads/extraction.

Check an individual downloaded file in Windows PowerShell:

```powershell
Get-FileHash -Algorithm SHA256 -LiteralPath 'C:\Downloads\EXACT-RELEASE-FILENAME'
```

Compare the result with the manifest entry for that exact file. Linux users can
run `sha256sum -c SHA256SUMS` from a directory containing the listed files.
Checksums detect corruption; verify that the manifest itself came from the
intended repository/release.

Mount or extract the complete ISO. Its `image/` directory contains the actual
flash image (`.img.gz`). Drivers, source and documentation are separate payloads.
Do not confuse that flash image with the ISO container.

## 2. Write the eMMC

**This erases the selected target.** Back it up first. Disconnect unrelated USB
drives where practical, then identify the eMMC reader by model and capacity.

1. Shut down the Pi cleanly and disconnect power.
2. Attach the removable eMMC to a compatible USB reader and connect it to the PC.
   If Windows offers to format existing Linux partitions, cancel.
3. Start Etcher and select **Flash from file**. Choose the inner `.img.gz`, or
   decompress it and choose `.img` if your writer requires that.
4. Choose **Select target** and independently verify the correct eMMC device.
   Never select the PC's system disk. Do not override a system-drive warning
   without positively identifying the device.
5. Choose **Flash**, let the write and validation complete, and safely eject.
6. Refit the eMMC with Pi power disconnected. Remove the recovery SD for the
   first eMMC boot. Connect Ethernet, then power on and allow first boot to finish.

If the eMMC stays inside the Pi, it cannot be flashed from PC Etcher over normal
Ethernet/SSH. Boot a separate recovery Linux SD, identify the eMMC from current
`lsblk` output and unmount its partitions. Do not assume `mmcblk0` or `mmcblk1`
always identifies eMMC. Do not write the currently mounted root filesystem.
A recovery flashing command is deliberately not supplied until the actual target
has been positively identified.

## 3. First boot and checks

The image is intended to generate fresh machine identity/SSH host keys and expand
the root partition on first boot. These behaviours still require fresh-image
qualification. The candidate's convenience login is `oem` / `orangepi`, with root
password login disabled. Its password was checked in the candidate filesystem.
Use `sudo` with the same password for administrator commands.
**Change the default password immediately** using `passwd` and never
expose default-password SSH to the Internet. Find the new address in your router's
DHCP list; do not assume the development board's address.

After login, check:

```sh
uname -r
lsblk -o NAME,SIZE,MODEL,TRAN,FSTYPE,MOUNTPOINTS
orangepi-update-guard status
orangepi-npu doctor
orangepi-npu verify --runs 10
```

Use the acceleration-report app for native tests. Its success is not proof of
YouTube/browser decoding. Connect Wi-Fi using your own credentials; select the
correct regulatory country. Pair Bluetooth through the normal desktop with a
matching code; range and other profiles still have known limitations.

If boot/display/network fails, power down cleanly where possible and return to
the known-working recovery SD. Preserve the failing image/logs for diagnosis;
do not repeatedly rewrite bootloaders or overwrite another disk by guesswork.

## SSD storage and boot status

Read-only inspection on 17 October 2026 confirmed these installed kernel modules:

```
kernel/drivers/nvme/host/nvme.ko.zst
kernel/drivers/usb/storage/uas.ko.zst
```

PCIe root bridges enumerated, but no NVMe controller or SSD block device appeared.
Only the eMMC supplied the running root/boot filesystems. Driver availability is
not equivalent to tested hardware detection, performance or boot compatibility.

| Use | Current status |
|---|---|
| Compatible NVMe SSD for data | Expected capability; not yet tested on this build |
| USB-connected SSD for data | Storage driver present; specific bridge/drive not tested |
| Root/boot on NVMe or USB | Not qualified; needs bootloader/initramfs/root configuration tests |
| First-boot expansion on SSD | Current helper handles eMMC only |
| Existing Windows/BitLocker SSD | Preserve data; filesystem/encryption needs separate handling |

Check the exact SSD model, connector, protocol and power requirements before
buying or attaching it. M.2 is a physical form factor, not proof that a SATA
device can operate in an NVMe-only configuration. Do not change SPI firmware
or format a drive merely to make it appear. No such changes are made by this repo.

For initial qualification, keep eMMC as boot/root, attach a compatible SSD with
power disconnected, and begin with non-destructive detection/health checks.
Read/write or destructive benchmarks require an explicitly chosen disposable
test location and a verified backup.
