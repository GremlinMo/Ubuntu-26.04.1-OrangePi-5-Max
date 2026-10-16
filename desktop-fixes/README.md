# Orange Pi desktop integration

## Current status — 2026-10-17

The acceleration report now includes packaged NPU inference and dynamically
discovers the H.264 device. Bluetooth pairing/A2DP succeeded in a controlled
test; range remains unresolved. The historical notes below describe October 13,
not the latest Bluetooth/NPU result. See the front-page hardware table and
`../docs/mainline-hardware-support.md` for current status.

The historical player source still ranks `v4l2slvideo1h264dec`, whereas the latest
boot enumerated the H.264 decoder at video3. Its launch/file-picker fix works,
but this ranking does not guarantee H.264 hardware selection on every boot.
The separately tested benchmark/report does not have that fixed-node assumption.
Player screen/audio output remains unqualified while the board is headless.

## Historical installation notes — 2026-10-13

Desktop changes were installed on the live Ubuntu board with permission; they
did not change kernel, Wi-Fi, firmware, boot configuration, current clock profile,
or update policy. A separately approved Bluetooth firmware alias was added later,
as described below; the controller now confirms that it loaded.
Original launcher files are backed up in
`/var/backups/orangepi-desktop-20261013` on Ubuntu.

## Using the apps

- **Orange Pi Accelerated Video Player** now opens a file chooser when started
  from the app menu. It prefers the tested H.264/HEVC hardware elements and GL
  output. Unsupported codecs may still decode in software. Actual screen/audio
  playback remains a user test, not proven by the launcher mock tests.
- **Orange Pi Balanced Mode / Performance Mode** use the existing authorized
  administrator helper and now show success/failure dialogs. They are one-shot
  actions, not permanent windows. Canceling authentication does not apply a mode.
- **Orange Pi Acceleration Report** checks the actual GLES renderer, lists
  PanVK/decoder support, shows temperatures and fan/cooling states, and offers
  short native-output decoder and CPU benchmarks. It has a 75°C load-test guard.
  Save Report exports an HTML evidence file with no SSID, IP/MAC address, or
  password. Take an ordinary GNOME screenshot of its window to share results.
- Reopen **Settings → Appearance** to see ChatGPT Aurora, Forge, and Night Sky.
  Registration does not replace your currently chosen wallpaper.

Report benchmarks are short synthetic workloads, not sustained playback or a
matched Raspberry Pi 5 comparison. PanVK device enumeration is not a Vulkan
game benchmark. Rocket NPU initialization is not inference or RKNN support.

## Known remaining issues

Bluetooth's UART driver recognizes SYN43711A0 but asks for
`brcm/BCM.xunlong,orangepi-5-max.hcd`. The matching vendor HCD exists at
`/lib/firmware/SYN43711A0.hcd`, not at the requested name. Its patch therefore
did not load during the original boot. With separate approval, the byte-identical
board-specific firmware alias was installed and the approved reboot confirmed
patched build 1000. Discovery still finds no devices, including the user's
phone whose visible Bluetooth settings screen was supplied. Controller tracing
shows successful classic/LE scan commands but no received device reports.
Bluetooth radio discovery/pairing therefore remains unresolved.

The first reboot exposed dracut loading the AP6611 Wi-Fi driver before GPIO
and SDIO readiness. The `system/orangepi-wifi-*` files and
`bin/orangepi-wifi-ready` fix that ordering without replacing the kernel/DTB.
Installation is separately backed up in
`/var/backups/orangepi-wifi-boot-order-20261013`. The second approved reboot
passed and automatically reconnected the saved 5-GHz Wi-Fi network.

The supplied YouTube screenshot is 1280×720 at 60 fps, VP9, with 225 dropped
frames out of 2935. It is not evidence of 4K or hardware decoding. The later
smooth 4K-over-Wi-Fi result is user-reported; codec/decoder details still need
capture. This installed GStreamer V4L2 plugin has no VP9 decoder element.

The old ISO/image release does **not** yet contain this desktop follow-up.
Refresh the release after hardware validation; do not describe the old ISO as
containing these fixes.
