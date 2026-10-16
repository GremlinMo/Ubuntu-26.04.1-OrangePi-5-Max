# Orange Pi 5 Max Ubuntu 26.04.1 mainline hardware status

Tested on the eMMC image with Ubuntu generic kernel `7.0.0-38-generic` and the Orange Pi 5 Max mainline device tree.

| Device | Status | Evidence / limitation |
|---|---|---|
| Mali-G610 GPU | Working with acceleration | Panthor bound; PanVK reports Mali-G610 MC4; Panfrost reports OpenGL ES 3.1. |
| Rockchip NPU | Packaged runtime installed; 8-bit MobileNet inference verified | On 2026-10-17 `orangepi-npu-runtime` 1.0.0 was installed in an isolated root-owned `/opt` prefix, with CLI and Orange Pi NPU desktop entry. Qualification observed 12 successful Rocket submissions; top class matched CPU with maximum 1 quantization-step difference. Same-A76 single-thread medians: CPU 46.38 ms / NPU 12.84 ms. System Python, graphics libraries and kernel unchanged. Other models/precision modes, multi-core scaling and 6 TOPS unverified. See `npu-integration-20261017.md`. Old ISO not refreshed. |
| Ethernet | Working | RTL8125 uses `r8169`; link came up at 1 Gbps during the audit. |
| eMMC | Working | 58.3 GiB device is mounted as the Ubuntu root filesystem. |
| Wi-Fi / AP6611S | 5-GHz connection/startup verified; overnight stability unresolved | Corrected DTB uses resolved pin references, GPIO2 PC5 reset and RTC CLKOUT; four-bit SDIO operates at 150 MHz and 1.8 V. SYN43711 firmware/NVRAM/CLM load. User reports stable short 5-GHz playback; the repaired startup passed the 2026-10-13 reboot. Known-source 2.4-GHz scan reception at 2412 MHz is also verified, but association/throughput are untested. On 2026-10-14 the board was found disconnected after overnight supplicant timeouts/authentication failures. One approved ordinary saved-profile reconnect succeeded at 5745 MHz without a password prompt/profile change; long-idle recovery is not yet fixed. |
| Bluetooth | Pairing, bonding, A2DP connection and active audio stream verified; usable range unresolved | Bluetooth-only `max-speed=1500000` DTB selected with recovery entries retained; firmware build 1000, hardware_error 0. On 2026-10-17 the corrected authorization helper observed a manually confirmed bond, resolved services, authorized A2DP and an active MediaTransport1; sampled connection lasted 123 seconds. Audible Pi output, sustained reliability, Hands-Free and other profiles remain unverified. The bounded test removed its new bond and restored settings. Both earlier Arch and Ubuntu trials had poor practical range. Current/maximum connected-link TX power both reported +8 dBm; actual RF output and supply droop are unmeasured. See `bluetooth-research-20261013/Ubuntu-media-success-20261017.json`. Old release images do not include this candidate. |
| Analog audio | Enumerated | ES8328 playback and capture devices are present. |
| HDMI audio | Enumerated | HDMI0 and HDMI1 ALSA devices are present; playback needs a connected HDMI sink for a real output test. |
| VPU decode/encode | Kernel devices present | RKVDEC, Hantro, VEPU, AV1, and RGA nodes are present; GStreamer stateless V4L2 codec plugins are installed. |
| USB | Host controllers working | USB 1.x/2.0/3.x root hubs enumerate; no external USB peripheral was attached for device-specific testing. |
| Thermal monitoring | Working | Package, CPU clusters, GPU, and NPU thermal zones report temperatures. |
| HDMI/display | DRM initialized | Rockchip DRM and both HDMI controllers bind; no display EDID was present during the headless SSH audit. |
| Camera/CSI | Not tested | No camera was attached. |
| NVMe/PCIe storage | Not tested / absent | No NVMe device was enumerated during this run. |

The vendor 5.10 fallback remains available for Rockchip's vendor MPP/NPU paths, but the preferred default is the generic 7.0 profile because it provides the working Panthor/Panfrost/PanVK graphics stack.
