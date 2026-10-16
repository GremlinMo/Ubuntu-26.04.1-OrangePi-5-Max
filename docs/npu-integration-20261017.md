# NPU everyday runtime integration — 17 October 2026

Installed `orangepi-npu-runtime` 1.0.0 on the Ubuntu eMMC installation, kernel
7.0.0-38-generic. Package size 44,153,308 bytes; installed-size metadata about
230 MiB. The isolated `/opt/orangepi-npu` prefix is root-owned, without writable
regular files for group/other users. No maintainer scripts, new service, port,
permission relaxation, kernel/firmware change or reboot was used.

The package embeds pinned Python 3.11.17, TFLite Runtime 2.14.0, NumPy 1.26.4,
Pillow 11.3.0 and the already-qualified Ubuntu Mesa Teflon delegate 26.0.8.
It does not replace system Python or GPU/video Mesa libraries. Apt simulation
showed one new package, zero upgrades/removals; `dpkg -i` installed only that
package plus normal desktop-menu triggers. Private dependency security updates
must be maintained explicitly; they are not managed by system Python updates.

## User interface

- App menu: **Orange Pi NPU**, offering verification, own-image classification,
  bundled demo and runtime health check through Zenity dialogs.
- CLI: `orangepi-npu doctor`, `demo`, `classify PHOTO`, `verify --json`.
- Photographs stay local; the model is bundled. No downloads during inference.
- NPU mode requires Rocket access and delegated partitions, with no automatic
  CPU-only retry. CPU reference mode is explicit. Unsupported graph portions may
  still use the CPU. This is not a general RKNN or chatbot runtime.
- Root invocation is refused; an unprivileged account without render access was
  tested and received a clear permission error. Existing OEM permissions suffice.
- Input, temperature and 120-second timeout guards are active. Integrity checks
  cover all packaged runtime files; a health check is not proof of inference.

## Validation

Nine hardware-free tests passed, covering numerical comparison failure cases,
checksum tampering, missing device access, health-status wording, GUI cancellation
and safe argument handling for image paths. Desktop-file syntax validation passed.
The Zenity window layout has not been visually verified in this integration run.

Actual installed-package qualification, as UID 1000:

- 12 successful Rocket submit ioctls, zero failed/unparsed submit completions.
- Rocket delegate selection observed; two graph partitions delegated.
- CPU and NPU classify the sample as Shih-Tzu, index 156.
- Maximum CPU/NPU difference: one output quantization step (limit two).
- Matched CPU4/A76, single-thread, 3 warmups + 20 measured invocations:
  CPU median 46.3809 ms; NPU median 12.8363 ms; ratio 3.6132x.
- Peak sampled temperature during qualification: 45.307 C. Not a thermal soak.
- Classification command works independently; missing-image error exits nonzero.

Evidence: `../drivers/npu/runtime-1.0.0/installed-qualification.json`.
Raw syscall traces were processed in memory and not retained. Timings exclude
image preparation and model startup/compilation. This is a single model/sample,
not all-model accuracy, optimized-CPU benchmarking, 6 TOPS or all-core scaling.

## Acceleration report integration and regression checks

The report now checks the installed runtime and runs a CPU/NPU comparison when
Benchmark is selected. It no longer claims inference is untested. Its earlier
files are backed up under `/var/backups/orangepi-npu-integration-20261017`.

The first full regression run found a pre-existing fixed-name decoder assumption:
it requested `v4l2slvideo1h264dec`, but this boot enumerates rkvdec at video3.
Only report/benchmark discovery was corrected: discover the V4L2 H.264 factory
and prefer the node whose sysfs name is rkvdec. No video driver/library changed.
The second full self-test passed: hardware GLES (182.08 FPS), H.264 180/180 frames
(293.79 FPS), HEVC 120/120 (189.05 FPS), AV1 60/60 (523.61 FPS), CPU tests, and
NPU comparison (13.16 ms versus CPU 46.31 ms). These short rates are not display
refresh rates, sustained-movie guarantees or Raspberry Pi comparisons.

Protected boot hashes remained unchanged:

- Image: `909bb80c7134de90492f0bb9123b5fce8dd3ea88c4e833a3ccfe2e36e8f9ee8f`
- initramfs: `fb71fd69e652ebcaeae97273923768d653780d787066c18d8800db4387e27869`
- extlinux.conf: `72e82c7e8a3eeac0d9d785d582a686d3ff624b64044dc5528f82c53199a20aaf`

GPU packages remain 26.0.8-1ubuntu0.3 and Wi-Fi DKMS remains
101.10.591.52.27-6+opi5max1. The regression report confirms connected 5-GHz Wi-Fi.

## Package and maintenance

Local installer: `../drivers/npu/runtime-1.0.0/orangepi-npu-runtime_1.0.0_arm64.deb`.
SHA256: `88e3ce45ab485f1705f87d01429b19899ac0b7b6bbae4ee5c947fc0d25928cbb`.
Sources and hash-pinned builder are in `../npu-package` with original notices.
Removal: `sudo apt remove orangepi-npu-runtime`; no driver removal is included.
The report remains installed and handles an absent runtime gracefully.
The package has been installed and tested, but an uninstall/reinstall cycle,
fresh-image installation, reboot retest and physical desktop interaction are
not claimed. The existing ISO has NOT been rebuilt.
