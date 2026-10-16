# AP6611S / SYN43711 Wi-Fi

`source/bcmdhd-sdio-101.10.591.52.27-6/` contains the complete patched DKMS
source. `ap6611-linux7.patch` records the corresponding source changes. Preserve
the source-file licences; these are not MIT-relicensed vendor sources.

Tested package version: `101.10.591.52.27-6+opi5max1`, kernel `7.0.0-38-generic`.
The patch addresses kernel interfaces and event/scan allocation compatibility.
This is not a claim of compatibility with every newer kernel.

The board also requires a correct Orange Pi 5 Max device tree, matching vendor
firmware/NVRAM/CLM, and late module loading after Rockchip GPIO/SDIO readiness.
See `../../desktop-fixes/bin/orangepi-wifi-ready` and the associated system files.
The eMMC-root initramfs omits the vendor Wi-Fi modules; the readiness service
loads them after their dependencies appear. These files are source references,
not an installer that should be blindly run on another OS.

Current 5-GHz connection and repaired boot startup are verified. 2.4-GHz scan
reception was observed, but association and throughput are untested. Overnight
disconnect/recovery remains unresolved. Use the appropriate regulatory country;
do not increase radio power beyond regulatory or hardware limits.

Firmware is withheld pending exact redistribution permission; see
`../../THIRD_PARTY_NOTICES.md`. No private network profiles or keys are included.
